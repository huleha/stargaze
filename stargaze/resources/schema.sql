create table roads (
    ref bigint primary key,
    shape geography(LineString) not null,
    type text not null,
    lit text
);

create table land (
    ref bigint primary key,
    shape geography(Polygon) not null,
    type text not null
);
