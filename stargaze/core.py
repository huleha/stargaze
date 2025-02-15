"""Core application logic."""

from functools import partial
from textwrap import dedent

from wkt import Box

import psycopg2

from stargaze import wkt
from stargaze.commons import BoundingBox, Coordinates
from stargaze.land_importer import LandImporter
from stargaze.relief_importer import ReliefImporter
from stargaze.road_importer import RoadImporter
from stargaze.sessions import SessionFactory

_session_factory = SessionFactory.get_instance()

_importers = [LandImporter(), ReliefImporter(), RoadImporter()]

with open('resources/scripts/missing_tiles.sql', 'r') as file:
    _missing_tiles_query = file.read();


def identify_missing_tiles(origin: Coordinates, radius: float) -> list[
    BoundingBox]:
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
            tiles = cursor.fetchall()
    return tiles


def import_tiles(missing_tiles) -> None:
    """Runs all importers on the extent of the tiles if any provided."""
    if not missing_tiles:
        print('nothing to be imported')
        return

    _, south, west, north, east = missing_tiles
    bounds = BoundingBox(
        minlat=min(south),
        minlon=min(west),
        maxlat=max(north),
        maxlon=max(east)
    )
    for importer in _importers:
        with _session_factory.session_scope() as session:
            print(f'running {type(importer).__qualname__} on {bounds}')
            importer.run(bounds, session)

    confirm_tile_import(missing_tiles)


def confirm_tile_import(tiles) -> None:
    """Add the tiles to the table of present tiles"""
    _insert_tiles = 'insert into tiles (geohash, bbox) values(%s, %s)'
    new_rows = [
        (row[0], Box(
            south=row[1],
            west=row[2],
            north=row[3],
            east=row[4]
        )) for row in tiles]
    with _session_factory.session_scope() as session:
        with session.cursor() as cursor:
            cursor.executemany(
                _insert_tiles,
                new_rows
            )


def stargaze(origin: Coordinates, radius: float, direction: float) -> list[
    Coordinates]:
    missing_tiles = identify_missing_tiles(origin, radius)
    print(f'there are {len(missing_tiles)} missing tiles')

    import_tiles(missing_tiles)

    # TODO: execute the script and find the stargazing spot

    return []


__all__ = ['stargaze']
