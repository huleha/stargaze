create table roads (
    ref bigint primary key,
    shape geography(LineString) not null,
    type text not null,
    lit text
);
