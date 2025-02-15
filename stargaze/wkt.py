"""Utilities for Well-Known Text primitives construction.

This module provides utilities to construct representations of spacial objects
in Well-Known Text (WKT) format. It is meant to be a simple utility module for
this project and does not make an effort to respect differences between WKT and
PostGIS's EWKT, support coordinates with the third dimension Z and measurement
label M, nor be complete. After constructing an object, the textual
representation can be obtained by calling `str` with this object."""


from stargaze.commons import Coordinates


class Box:

    def __init__(self, *, south: float, west: float, north: float, east: float):
        if east < west or north < south:
            raise ValueError()
        self.south = south
        self.west = west
        self.north = north
        self.east = east

    def __str__(self):
        return f'Box({self.west} {self.south}, {self.east} {self.north})'


class Point:

    def __init__(self, point: Coordinates):
        self.point = point

    def __str__(self):
        return 'Point({point})'.format(point=_point(self.point))


class LineString:

    def __init__(self, path: list[Coordinates]):
        self.path = path

    def __str__(self):
        return 'LineString{points}'.format(points=_point_string(self.path))


class LinearRing:

    def __init__(self, path: list[Coordinates]):
        self.path = path

    def __str__(self):
        return 'LinearRing{points}'.format(points=_point_string(self.path))


class Polygon:

    def __init__(self, shell: list[Coordinates]):
        self._rings = [shell]

    def hole(self, hole: list[Coordinates]):
        """Adds a hole to this polygon."""
        self._rings.append(hole)
        return self

    def holes(self, holes: list[list[Coordinates]]):
        """Adds a list of holes to this polygon."""
        self._rings.extend(holes)
        return self

    def __str__(self):
        # polygon((shell), (hole), (hole), ...)
        return 'Polygon({rings})'\
            .format(rings=', '.join(map(_point_string, self._rings)))


def _point(point: Coordinates) -> str:
    return '{lon} {lat}'.format(lon=point.lon, lat=point.lat)

def _point_string(path: list[Coordinates]) -> str:
    return '(' + ', '.join(map(_point, path)) + ')'


__all__ = ['Box', 'Point', 'LineString', 'LinearRing', 'Polygon']
