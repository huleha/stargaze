-- begin;

create temp table params (
    origin geography,
    radius int,
    calm_road_buffer int,
    busy_road_buffer int
) on commit drop;

create temp table patches (
    centre geometry
) on commit drop;

create temp table lights (
    centre geometry,
    area float
) on commit drop;

insert into params values(
    ST_GeomFromText(%(origin)s, 4326)::geography,
    %(radius)s,
    200,
    500);

with search as (select
    utm_zone(origin::geometry) as zone,
    ST_Buffer(origin, radius)::geometry as area
    from params),
calm_roads_buffer as (
    select coalesce(
        ST_Union(ST_Buffer(roads.shape, calm_road_buffer)::geometry),
        ST_GeomFromText('POINT EMPTY', 4326)) as calm_roads_buffer
    from roads, params
    where
        roads.type in ('tertiary', 'unclassified', 'residential', 'track', 'road')
        and ST_DWithin(roads.shape, origin, radius)
        and not (coalesce(roads.lit, 'no') in ('yes', '24/7'))),
busy_roads_buffer as (
    select coalesce(
        ST_Union(ST_Buffer(roads.shape, busy_road_buffer)::geometry),
        ST_GeomFromText('POINT EMPTY', 4326)) as busy_roads_buffer
    from roads, params
    where
        roads.type in ('motorway', 'trunk', 'primary', 'secondary')
        and ST_DWithin(roads.shape, origin, radius)),
ineligible_area as (
    select coalesce(
        ST_Union(land.shape::geometry),
        ST_GeomFromText('POINT EMPTY', 4326)) as ineligible_area
    from land, params
    where ST_DWithin(land.shape, origin, radius)),
accessible_area as (
    select ST_Intersection(
        ST_Difference(
            ST_Difference(calm_roads_buffer, ineligible_area),
            busy_roads_buffer),
        search.area) as accessible_area
    from calm_roads_buffer, busy_roads_buffer, ineligible_area, search),
hillshade as (
    select ST_HillShade(
        ST_Union(tile), 1, '8BUI', 218, 11) as hillshade
    from relief_tiles, search
    where ST_Intersects(
        ST_Envelope(tile),
        search.area)),
suitable_area as (
    select dump.geom as patch
    from
        accessible_area,
        hillshade,
        ST_DumpAsPolygons(
            ST_Reclass(
                ST_Clip(hillshade, accessible_area, 0),
                1, '0-255:0', '8BUI', 255)) as dump)
insert into patches
    select ST_Centroid(patch) as centre
    from suitable_area
    where ST_Area(patch::geography) > 300000.0;

insert into lights
    select ST_Centroid(shape)::geometry as centre, area
    from params, residential_area
    where
        ST_DWithin(shape, origin, radius)
        and area > 5000.0;

with ranked as (
    select
        patches.centre as spot,
        sum(
            lights.area
            / ((patches.centre <-> lights.centre) ^ 2)
        ) as disruption
    from patches, lights
    group by patches.centre
    order by disruption asc
    limit 5)
-- select ST_AsGeoJSON(ST_Collect(spot))
select ST_X(spot) as lon, ST_Y(spot) as lat
from ranked;

-- commit;
