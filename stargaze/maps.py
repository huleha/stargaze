from enum import Enum
from typing import Literal

import requests
from pydantic import BaseModel, Field

from stargaze.coordinates import Coordinates


class Feature(BaseModel):
    type: str
    id: int
    tags: dict[str, str] | None

class Node(Feature):
    type: Literal['node']
    lat: float
    lon: float

class Bounds(BaseModel):
    minlat: float
    minlon: float
    maxlat: float
    maxlon: float

class Way(Feature):
    type: Literal['way']
    bounds: Bounds | None
    nodes: list[int] | None
    geometry: list[Coordinates] | None

class MultipolygonRole(str, Enum):
    INNER = 'inner'
    OUTER = 'outer'

class Member(BaseModel):
    type: Literal['way']
    ref: int
    role: MultipolygonRole
    geometry: list[Coordinates] | None

class MultipolygonRelation(Feature):
    type: Literal['relation']
    bounds: Bounds | None
    members: list[Member]

class OverpassResponse(BaseModel):
    version: float
    generator: str
    osm3s: dict[str, str]
    elements: list[Node | Way | MultipolygonRelation]


def main():
    endpoint = 'https://overpass-api.de/api/interpreter'
    query = '''
        [out:json];
        rel
            [landuse=residential]
            [type=multipolygon]
            (around:50,50.0211149,19.8831563);
        out geom;'''
    response = requests.get(endpoint, data=query)
    response.raise_for_status()
    extract = OverpassResponse.model_validate_json(response.text)
    print(extract.model_dump())


if __name__ == '__main__':
    main()
