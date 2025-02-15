"""Core application logic."""

from functools import partial
from textwrap import dedent

import psycopg2

from stargaze import wkt
from stargaze.commons import BoundingBox, Coordinates
from stargaze.land_importer import LandImporter
from stargaze.relief_importer import ReliefImporter
from stargaze.road_importer import RoadImporter
from stargaze.sessions import SessionFactory


_session_factory = SessionFactory.get_instance()

_importers = [LandImporter(), ReliefImporter(), RoadImporter()]

def identify_missing_tiles(origin: Coordinates, radius: float) -> list[BoundingBox]:
    """Returns a list of missing tiles for a given search area.

    Queries the database for tiles overlapping with the search area given by
    `origin` and `radius` and returns a list of bounding boxes of tiles which
    are covered by the desired search area, that is needed for the query, but
    are not present in the database and hence have to be downloaded."""

    with _session_factory.session_scope() as session:
        with session.cursor() as cursor:
            cursor.execute(
                _missing_tiles_query,
                {'origin': str(wkt.Point(origin)), 'radius': radius}
            )
            tiles = []
            for south, west, north, east in cursor:
                tiles.append(
                    BoundingBox(
                        minlat=south,
                        minlon=west,
                        maxlat=north,
                        maxlon=east
                    )
                )
    return tiles


def import_tile(bounds: BoundingBox) -> None:
    """Runs all importers on given bounds."""
    for importer in _importers:
        with _session_factory.session_scope() as session:
            print(f'running {type(importer).__qualname__} on {bounds}')
            importer.run(bounds, session)


def stargaze(origin: Coordinates, radius: float, direction: float) -> list[Coordinates]:
    missing_tiles = identify_missing_tiles(origin, radius)
    print(f'there are {len(missing_tiles)} missing tiles')
    for tile in missing_tiles:
        print(f'importing tile {tile}')
        import_tile(tile)
    return []


__all__ = ['stargaze']
