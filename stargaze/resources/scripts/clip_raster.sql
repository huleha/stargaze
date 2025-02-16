with params as (
    select
        ST_Envelope(relief.rast) as envelope
    from
        relief),
grid as (
    select
        ST_Geohash(ST_Centroid(tile),5) as geohash,
        Box2D(ST_Envelope(tile)) as bbox,
        grid.tile as tile
    from
        params,
        ST_SquareGrid(180/(2^12), params.envelope) as grid(tile))
insert into relief_tiles(geohash, bbox, tile)
select
    grid.geohash,
    grid.bbox,
    ST_Clip(relief.rast, grid.tile)
from
    relief,
    grid
on conflict (geohash) do update
set tile = excluded.tile
;

delete from relief;
