from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class BoundingBox:
    minlat: float
    minlon: float
    maxlat: float
    maxlon: float

    def __str__(self):
        # south,west,north,east
        return ','.join(
            map(
                str,
                [
                    self.minlat,
                    self.minlon,
                    self.maxlat,
                    self.maxlon
                ]
            )
        )


@dataclass(frozen=True, kw_only=True)
class Coordinates:
    lat: float
    lon: float


__all__ = ['BoundingBox', 'Coordinates']
