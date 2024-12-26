from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field
import requests

from stargaze.commons import BoundingBox, Coordinates


_endpoint = 'https://overpass-api.de/api/interpreter'


class Feature(BaseModel):
    type: str
    id: int
    tags: dict[str, str]

class Node(Feature, Coordinates):
    type: Literal['node']

class Way(Feature):
    type: Literal['way']
    bounds: BoundingBox
    nodes: list[int]
    geometry: list[Coordinates]

    def is_closed(self) -> bool:
        """Returns whether this way is closed."""
        return self.nodes[0] == self.nodes[-1]

class MultipolygonRole(str, Enum):
    INNER = 'inner'
    OUTER = 'outer'

class Member(BaseModel):
    type: Literal['way']
    ref: int
    role: MultipolygonRole
    geometry: list[Coordinates]

class Multipolygon(Feature):
    type: Literal['relation']
    bounds: BoundingBox
    members: list[Member]

class OverpassResponse(BaseModel):
    version: float
    generator: str
    osm3s: dict[str, str]
    elements: list[Node | Way | Multipolygon]


def query(query: str, endpoint: str | None = None) -> OverpassResponse:
    """Sends query to endpoint and returns deserialized response.

    This function sends the given OverpassQL query to the given endpoint (Main
    Overpass API instance by default), deserializes the response and returns it
    as an `OverpassResponse` instance. For simplicity, all geometry-related
    fields are required and multipolygon relations are the only supported type
    of relations, so make sure to always use `out geom` in queries and
    additionally specify `[type=multipolygon]` when querying relations."""

    response = requests.get(endpoint or _endpoint, data=query)
    response.raise_for_status()
    return OverpassResponse.model_validate_json(response.text)


__all__ = [
    'Feature', 'Node', 'Way', 'MultipolygonRole', 'Member', 'Multipolygon',
    'OverpassResponse', 'query'
]
