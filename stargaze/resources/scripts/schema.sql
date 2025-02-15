begin transaction;

-- required for the container, where stargaze is superuser
-- create extension if not exists postgis;
-- create extension if not exists postgis_raster;

create table if not exists land (
    ref bigint primary key,
    shape geography(Polygon, 4326) not null,
    type text not null
);

-- table for inserting and temporarily storing rasters
create table if not exists relief (
    rast raster not null
);

create table if not exists relief_tiles (
    geohash character(5) primary key,
    bbox box2d not null,
    tile raster not null
);

create table if not exists roads (
    ref bigint primary key,
    shape geography(LineString, 4326) not null,
    type text not null,
    lit text
);

create table if not exists tiles (
    geohash character(5) primary key,
    bbox box2d not null
);

create or replace function clip_raster()
returns trigger as $$
begin
    with params as (
        select
            st_envelope(relief.rast) as envelope
        from
            relief
    ),
    grid as (
        select
            st_geohash(tile,5) as geohash,
            box2d(st_envelope(tile)) as bbox,
            grid.tile as tile
        from
            params,
            st_squaregrid(180/(2^12), params.envelope) as grid(tile)
    )
    insert into relief_tiles(geohash, bbox, tile)
    select
        grid.geohash,
        grid.bbox,
        st_clip(relief.rast, grid.tile)
    from
        relief,
        grid;

    delete from relief;

    return null;
end;
$$ language plpgsql;

create or replace function utm_zone(point geometry)
returns integer as $$
declare
    prefix integer;
    zone integer;
begin
    if GeometryType(point) != 'POINT' then
        raise exception 'POINT expected, but % given', GeometryType(point);
    end if;
    if ST_SRID(point) != 4326 then
        raise exception 'SRID 4326 (WGS84) expected, but SRID % given', ST_SRID(point);
    end if;
    prefix = case
        when ST_Y(point) >= 0 then 32600  -- northern hemisphere
        else 32700  -- southern hemisphere
    end;
    zone = floor((ST_X(point) + 180) / 6) + 1;
    return prefix + zone;
end;
$$ language plpgsql
immutable
returns null on null input
parallel safe;

create or replace trigger raster_clipping_trigger
after insert on relief
for each row
execute function clip_raster();

commit;
