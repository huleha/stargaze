with params as (select
    ST_GeomFromText('Point(26.945 53.863)', 4326) as origin,
    15000 as radius
),
search_area as (
    select ST_Buffer(origin::geography, radius)::geometry as shape
    from params
)
select
    ST_GeoHash(grid.tile, 5) as geohash,
    ST_YMin(grid.tile) as south,
    ST_XMin(grid.tile) as west,
    ST_YMax(grid.tile) as north,
    ST_XMax(grid.tile) as east
from
    search_area,
    ST_SquareGrid(180/(2^12), search_area.shape) as grid(tile)
    left join tiles on ST_GeoHash(grid.tile, 5) = tiles.geohash
where
    ST_Intersects(grid.tile, search_area.shape)
    and tiles.geohash is null;
