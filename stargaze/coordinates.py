from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True, slots=True)
class Coordinates:
    lat: float
    lon: float
