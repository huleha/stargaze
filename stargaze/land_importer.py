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


class LandImporter(BaseImporter):
    """Importer of land classifying features from OverpassAPI."""

    _overpass_query_template = dedent("""\
        [out:json][bbox:%s];
        (
            way[landuse=construction];
            way[landuse=forest];
            way[landuse=military];
            way[natural=water];
            way[natural=wood];
        );
        out geom;""")

    _insert_stmt = dedent("""\
        insert into land (ref, shape, type)
        values %s
        on conflict (ref) do update set
            shape = excluded.shape,
            type = excluded.type;""")

    def __init__(self, endpoint: str | None = None):
        self._endpoint = endpoint

    @staticmethod
    def _classify(feature: overpass.Feature) -> str:
        """Classifies the feature based on its tags and returns its type."""
        # it's more of a sketch
        return feature.tags.get('landuse') or feature.tags.get('natural')

    def fetch(self, bounds: BoundingBox):
        overpass_query = self._overpass_query_template % str(bounds)
        return overpass.fetch(overpass_query, endpoint=self._endpoint)

    def transform(self, extract):
        data = []
        for feature in extract.elements:
            if feature.type == 'way':
                data.append({
                    'ref': feature.id,
                    'shape': str(wkt.Polygon(feature.geometry)),
                    'type': self._classify(feature)
                })
            elif feature.type == 'relation':
                raise NotImplementedError(
                    'areas represented as multipolygon relations are not'\
                    'supported yet'
                )
        return data

    def load(self, data, session):
        with session.cursor() as cursor:
            psycopg2.extras.execute_values(
                cur=cursor,
                sql=self._insert_stmt,
                argslist=data,
                template='(%(ref)s, %(shape)s, %(type)s)'
            )


def main():
    land_importer = LandImporter()
    bounds = BoundingBox(minlat=49.98, minlon=18.48, maxlat=50.02, maxlon=18.52)
    with open(_resources/'credentials.toml', 'rb') as credentials_file:
        credentials = tomllib.load(credentials_file)
    with psycopg2.connect(**credentials) as session:
        land_importer.run(bounds, session)


if __name__ == '__main__':
    main()
