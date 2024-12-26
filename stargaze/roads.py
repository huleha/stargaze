import importlib
import tomllib

import psycopg2
import psycopg2.extras

from stargaze import wkt
from stargaze.base_importer import BaseImporter
from stargaze.commons import BoundingBox
from stargaze.overpass import OverpassResponse, query


_resources = importlib.resources.files('stargaze.resources')


class RoadsImporter(BaseImporter):
    """Importer of roads from OverpassAPI."""

    def __init__(self, endpoint: str | None = None):
        self._endpoint = endpoint

    def fetch(self, bounds):
        overpass_query_template = (_resources/'roads.overpassql').read_text()
        # bounding box format: (south,west,north,east)
        bbox = ','.join(
            map(
                str,
                [bounds.minlat, bounds.minlon, bounds.maxlat, bounds.maxlon]
            )
        )
        overpass_query = overpass_query_template % {'bbox': bbox}
        return query(overpass_query, endpoint=self._endpoint)

    def transform(self, extract):
        return [
            {
                'ref': road.id,
                'shape': str(wkt.LineString(road.geometry)),
                'type': road.tags['highway'],
                'lit': road.tags.get('lit')
            } for road in extract.elements
        ]

    def load(self, data):
        with open(_resources/'credentials.toml', 'rb') as credentials_file:
            credentials = tomllib.load(credentials_file)
        with psycopg2.connect(**credentials) as session:
            stmt = (_resources/'insert_roads.sql').read_text()
            with session.cursor() as cursor:
                psycopg2.extras.execute_values(
                    cursor,
                    stmt,
                    data,
                    template='(%(ref)s, %(shape)s, %(type)s, %(lit)s)'
                )


def main():
    roads_importer = RoadsImporter()
    bounds = BoundingBox(minlat=50.0, minlon=18.0, maxlat=50.01, maxlon=18.01)
    roads_importer.run(bounds)


if __name__ == '__main__':
    main()
