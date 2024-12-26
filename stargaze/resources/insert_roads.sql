insert into roads (ref, shape, type, lit)
values %s
on conflict (ref) do update set
    shape=excluded.shape,
    type=excluded.type,
    lit=excluded.lit;
