"""Command-line interface."""


from argparse import ArgumentParser

import pint

from stargaze.geocoding import find_coordinates


ureg = pint.UnitRegistry()

_directions = {
    'north': 0.0, 'east': 90.0, 'south': 180.0, 'west': 270.0,
    'n': 0.0, 'nne': 22.5, 'ne': 45.0, 'ene': 67.5,
    'e': 90.0, 'ese': 112.5, 'se': 135.0, 'sse': 157.5,
    's': 180.0, 'ssw': 202.5, 'sw': 225.0, 'wsw': 247.5,
    'w': 270.0, 'wnw': 292.5, 'nw': 315.0, 'nnw': 337.5
}


def parse_length(length: str) -> float:
    """Parses textual representation of a length and returns its numeric value."""
    quantity = ureg(length)
    if not isinstance(quantity, pint.Quantity):
        return quantity
    if not quantity.check(ureg.meter):
        raise ValueError(f"The input '{length}' does not represent a length.")
    return quantity.to(ureg.meter).magnitude


def parse_direction(direction: str) -> float:
    """Parses textual direction and returns numeric azimuth."""
    return _directions.get(direction.casefold()) or float(direction)


def main():
    parser = ArgumentParser(
        prog='stargaze',
        description=\
            'stargaze helps you find the best spot for astronomical '\
            'observations.'
    )
    parser.add_argument(
        '--near', required=True, metavar='whereabouts',
        help='description of whereabouts, either coordinates or locality name'
    )
    parser.add_argument(
        '--within', default='1km', metavar='radius',
        help='search radius, e.g. "10km"'
    )
    parser.add_argument(
        '--head', metavar='direction',
        help=\
            'observation direction, either cardinal point or azimuth, e.g. '\
            '"south", "SE", "120.3"'
    )
    args = parser.parse_args()
    whereabouts = find_coordinates(args.near)
    radius = parse_length(args.within)
    direction = args.head and parse_direction(args.head)
    print(whereabouts, radius, direction, sep='\n')


if __name__ == '__main__':
    main()
