"""Core application logic."""

from functools import partial
from textwrap import dedent

import importlib
import psycopg2

from stargaze import wkt
from stargaze.commons import BoundingBox, Coordinates
from stargaze.land_importer import LandImporter
from stargaze.relief_importer import ReliefImporter
from stargaze.residential_area_importer import ResidentialAreaImporter
from stargaze.road_importer import RoadImporter
from stargaze.sessions import SessionFactory

_session_factory = SessionFactory.get_instance()

_importers = [
    LandImporter(), ReliefImporter(), ResidentialAreaImporter(), RoadImporter()
]

_scripts = importlib.resources.files('stargaze.resources.scripts')

with open(_scripts / 'missing_tiles.sql', 'r') as file:
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

    south = []
    west = []
    north = []
    east = []
    for tile in missing_tiles:
        south.append(tile[1])
        west.append(tile[2])
        north.append(tile[3])
        east.append(tile[4])
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
    _insert_tiles = 'insert into tiles (geohash, bbox) values(%s, %s::box2d)'
    new_rows = [
        (geohash, str(wkt.Box(south=south, west=west, north=north, east=east)))
        for geohash, south, west, north, east in tiles
    ]
    with _session_factory.session_scope() as session:
        with session.cursor() as cursor:
            cursor.executemany(
                _insert_tiles,
                new_rows
            )


def stargaze(origin: Coordinates,
             radius: float,
             azimuth: float) -> list[Coordinates]:
    missing_tiles = identify_missing_tiles(origin, radius)
    print(f'there are {len(missing_tiles)} missing tiles')
    import_tiles(missing_tiles)
    with open(_scripts / 'stargaze.sql') as file:
        stargaze_query = file.read()
    with _session_factory.session_scope() as session:
        with session.cursor() as cursor:
            cursor.execute(
                stargaze_query,
                {'origin': str(wkt.Point(origin)),
                 'radius': radius,
                 'azimuth': azimuth,
                 'altitude': 45}
            )
            spots = [Coordinates(lat=lat, lon=lon) for lon, lat in cursor]
        session.commit()
    return spots


__all__ = ['stargaze']


def main():
    stargaze(origin=Coordinates(lat=20, lon=30), radius=10000, direction=0)


if __name__ == '__main__':
    main()
