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

_missing_tiles_query = dedent("""\
    with params as (select
        ST_SetSRID(cast(%(origin)s as geometry), 4326) as origin,
        %(radius)s as radius
    ),
    search_area as (
        select ST_Transform(
            ST_Buffer(
                ST_Transform(params.origin, utm_zone(params.origin)),
                params.radius
            ),
            4326
        ) as shape
        from params
    ),
    searched_tiles as (
        select
            grid.tile as tile,
            ST_GeoHash(grid.tile, 5) as geohash
        from
            search_area,
            ST_SquareGrid(180/(2^12), search_area.shape) as grid(tile)
        where
            ST_Intersects(grid.tile, search_area.shape)
    )
    select
        ST_YMin(searched_tiles.tile) as south,
        ST_XMin(searched_tiles.tile) as west,
        ST_YMax(searched_tiles.tile) as north,
        ST_XMax(searched_tiles.tile) as east
    from
        searched_tiles
        left join land_tiles on searched_tiles.geohash = land_tiles.geohash
        left join road_tiles on searched_tiles.geohash = road_tiles.geohash
    where (
        land_tiles.geohash is null
        or road_tiles.geohash is null
    );""")


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
