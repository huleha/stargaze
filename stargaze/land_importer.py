from textwrap import dedent

import psycopg2
import psycopg2.extras

from stargaze import overpass
from stargaze import wkt
from stargaze.base_importer import BaseImporter
from stargaze.commons import BoundingBox
from stargaze.sessions import SessionFactory


class LandImporter(BaseImporter):
    """Importer of land classifying features from OverpassAPI."""

    _overpass_query_template = dedent("""\
        [out:json][bbox:%s];
        (
            way[landuse=construction];
            way[landuse=farmyard];
            way[landuse=forest];
            way[landuse=military];
            way[natural=water];
            way[natural=wood];
            rel[landuse=construction][type=multipolygon];
            rel[landuse=farmyard][type=multipolygon];
            rel[landuse=forest][type=multipolygon];
            rel[landuse=military][type=multipolygon];
            rel[natural=water][type=multipolygon];
            rel[natural=wood][type=multipolygon];
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
        refs = set()
        for feature in extract.elements:
            if (
                feature.type == 'way'
                and feature.is_closed()
                and feature.id not in refs
            ):
                data.append({
                    'ref': feature.id,
                    'shape': str(wkt.Polygon(feature.geometry)),
                    'type': self._classify(feature)
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
                            'shape': str(wkt.Polygon(member.geometry)),
                            'type': self._classify(feature)
                            #                      ^^^^^^^
                            # yes, feature, not member, members do not have tags
                        })
                        refs.add(member.ref)
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
    importer = LandImporter()
    bounds = BoundingBox(minlat=49.98, minlon=18.48, maxlat=50.02, maxlon=18.52)
    with SessionFactory.get_instance() as factory:
        with factory.session_scope() as session:
            importer.run(bounds, session)


if __name__ == '__main__':
    main()
