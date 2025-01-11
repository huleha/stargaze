"""Geocoding functionality.

This module exposes a single function `find_coordinates`, which looks up
coordinates corresponding to the given description of whereabouts given as a
string."""


from argparse import ArgumentParser
import re

import requests

from stargaze.commons import Coordinates


_format_handler_registry = {}


def find_coordinates(whereabouts: str) -> Coordinates:
    """Finds coordinates corresponding to given whereabouts.

    This function tries to identify the whereabouts description format and parse
    it accordingly. Raises `TypeError` when anything other than `str` is given
    and `ValueError` when it is impossible to determine coordinates by the given
    description."""

    if not isinstance(whereabouts, str):
        raise TypeError(
            'whereabouts must be str, but {type} was given'
            .format(type=type(whereabouts).__qualname__)
        )
    if len(whereabouts) == 0:
        raise ValueError('whereabouts must be a non-empty string')
    for pattern, format_handler in _format_handler_registry.items():
        match = pattern.fullmatch(whereabouts)
        if match is not None:
            return format_handler(match)
    raise ValueError(f'unsupported geocoding format for {whereabouts}')


def geocoding_format(pattern: str):
    """Decorator which registers the wrapped function with a given pattern.

    When `find_coordinates` is called, the given whereabouts string is tested
    against patterns one by one in the order they were declared. Upon match, the
    corresponding format handler is called with the obtained `re.Match` object,
    not the original string, so it is possible to capture groups in the pattern.
    However, if the original string is needed, it can be accessed via the
    `string` attribute of the match object."""

    def registering_decorator(format_handler):
        _format_handler_registry[re.compile(pattern)] = format_handler
        return format_handler
    return registering_decorator


@geocoding_format(r'[([]?(-?\d+\.\d+),\s*(-?\d+\.\d+)[)\]]?')
def decimal_degrees(match: re.Match) -> Coordinates:
    lat, lon = match.groups()
    return Coordinates(lat=float(lat), lon=float(lon))


@geocoding_format(r'.*')
def nominatim(match: re.Match) -> Coordinates:
    headers = {
        'User-Agent': 'stargaze/1.0 (https://github.com/huleha/stargaze)',
        'Referer': 'https://github.com/huleha/stargaze'
    }
    params = {'format': 'jsonv2', 'limit': 1}
    endpoint = "https://nominatim.openstreetmap.org/search"
    response = requests.get(
        endpoint,
        params={'q': match.string, **params},
        headers=headers
    )
    response.raise_for_status()
    feature = response.json()[0]
    return Coordinates(lat=float(feature['lat']), lon=float(feature['lon']))


__all__ = ['find_coordinates']


def main():
    parser = ArgumentParser(
        description='finds coordinates corresponding to given whereabouts.'
    )
    parser.add_argument('whereabouts')
    args = parser.parse_args()
    print(find_coordinates(args.whereabouts))


if __name__ == '__main__':
    main()
