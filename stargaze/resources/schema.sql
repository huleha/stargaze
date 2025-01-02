create table roads (
    ref bigint primary key,
    shape geography(LineString, 4326) not null,
    type text not null,
    lit text
);

create table land (
    ref bigint primary key,
    shape geography(Polygon, 4326) not null,
    type text not null
);

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
