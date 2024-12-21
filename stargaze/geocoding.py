"""Geocoding functionality.

This module exposes a single function `find_coordinates`, which looks up
coordinates corresponding to the given description of whereabouts given as a
string."""


import re

from stargaze.coordinates import Coordinates


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


@geocoding_format(r'.*')
def nominatim(match: re.Match) -> Coordinates:
    raise NotImplementedError()


__all__ = ['find_coordinates']
