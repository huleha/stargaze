from textwrap import dedent

import psycopg2
import psycopg2.extras

from stargaze import overpass
from stargaze import wkt
from stargaze.base_importer import BaseImporter
from stargaze.commons import BoundingBox
from stargaze.sessions import SessionFactory


class ResidentialAreaImporter(BaseImporter):
    """Importer of land classifying features from OverpassAPI."""

    _overpass_query_template = dedent("""\
        [out:json][bbox:%s];
        (
            way[landuse=residential];
            rel[landuse=residential][type=multipolygon];
        );
        out geom;""")

    _insert_stmt = dedent("""\
        insert into residential_area (ref, shape)
        values %s
        on conflict (ref) do update set
            shape = excluded.shape;""")

    def __init__(self, endpoint: str | None = None):
        self._endpoint = endpoint

    def fetch(self, bounds: BoundingBox):
        overpass_query = self._overpass_query_template % str(bounds)
        return overpass.fetch(overpass_query, endpoint=self._endpoint)

    def transform(self, extract):
        data = []
        refs = set()
        for feature in extract.elements:
            if (
                feature.type == 'way'
                and feature.is_closed()
                and feature.id not in refs
            ):
                data.append({
                    'ref': feature.id,
                    'shape': str(wkt.Polygon(feature.geometry))
                })
                refs.add(feature.id)
            elif feature.type == 'relation':
                for member in feature.members:
                    if (
                        member.role == overpass.MultipolygonRole.OUTER
                        and member.is_closed()
                        and member.ref not in refs
                    ):
                        data.append({
                            'ref': member.ref,
                            'shape': str(wkt.Polygon(member.geometry))
                        })
                        refs.add(feature.id)
        return data

    def load(self, data, session):
        with session.cursor() as cursor:
            psycopg2.extras.execute_values(
                cur=cursor,
                sql=self._insert_stmt,
                argslist=data,
                template='(%(ref)s, %(shape)s)'
            )


def main():
    importer = ResidentialAreaImporter()
    bounds = BoundingBox(minlat=49.98, minlon=19.88, maxlat=50.02, maxlon=19.92)
    with SessionFactory.get_instance() as factory:
        with factory.session_scope() as session:
            importer.run(bounds, session)


if __name__ == '__main__':
    main()
