from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class BoundingBox:
    minlat: float
    minlon: float
    maxlat: float
    maxlon: float


@dataclass(frozen=True, kw_only=True)
class Coordinates:
    lat: float
    lon: float


__all__ = ['BoundingBox', 'Coordinates']
