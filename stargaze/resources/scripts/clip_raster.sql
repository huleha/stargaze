with params as (
    select
        st_envelope(relief.rast) as envelope
    from
        relief),
grid as (
    select
        st_geohash(tile,5) as geohash,
        box2d(st_envelope(tile)) as bbox,
        grid.tile as tile
    from
        params,
        st_squaregrid(180/(2^12), params.envelope) as grid(tile))
insert into relief_tiles(geohash, bbox, tile)
select
    grid.geohash,
    grid.bbox,
    st_clip(relief.rast, grid.tile) as tile
from
    relief,
    grid
on conflict (geohash) do update
set tile = excluded.tile;

delete from relief;
