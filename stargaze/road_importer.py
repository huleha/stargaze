import importlib
import tomllib
from textwrap import dedent

import psycopg2
import psycopg2.extras

from stargaze import overpass
from stargaze import wkt
from stargaze.base_importer import BaseImporter
from stargaze.commons import BoundingBox


_resources = importlib.resources.files('stargaze.resources')


class RoadImporter(BaseImporter):
    """Importer of roads from OverpassAPI."""

    _overpass_query_template = dedent("""\
        [out:json][bbox:%s];
        (
            way[highway=motorway];
            way[highway=trunk];
            way[highway=primary];
            way[highway=secondary];
            way[highway=tertiary];
            way[highway=unclassified];
            way[highway=residential];
            way[highway=track];
            way[highway=road];
        );
        out geom;""")

    _insert_stmt = dedent("""\
        insert into roads (ref, shape, type, lit)
        values %s
        on conflict (ref) do update set
            shape = excluded.shape,
            type = excluded.type,
            lit = excluded.lit;""")

    def __init__(self, endpoint: str | None = None):
        self._endpoint = endpoint

    def fetch(self, bounds):
        overpass_query = self._overpass_query_template % str(bounds)
        return overpass.fetch(overpass_query, endpoint=self._endpoint)

    def transform(self, extract):
        return [
            {
                'ref': road.id,
                'shape': str(wkt.LineString(road.geometry)),
                'type': road.tags['highway'],
                'lit': road.tags.get('lit')
            } for road in extract.elements
        ]

    def load(self, data, session):
        with session.cursor() as cursor:
            psycopg2.extras.execute_values(
                cur=cursor,
                sql=self._insert_stmt,
                argslist=data,
                template='(%(ref)s, %(shape)s, %(type)s, %(lit)s)'
            )


def main():
    roads_importer = RoadImporter()
    bounds = BoundingBox(minlat=50.0, minlon=18.0, maxlat=50.01, maxlon=18.01)
    with open(_resources/'credentials.toml', 'rb') as credentials_file:
        credentials = tomllib.load(credentials_file)
    with psycopg2.connect(**credentials) as session:
        roads_importer.run(bounds, session)


if __name__ == '__main__':
    main()
