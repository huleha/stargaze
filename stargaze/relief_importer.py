import importlib
import os
import psycopg2
import requests
import subprocess
import tempfile
import tomllib

from dotenv import load_dotenv

from stargaze.base_importer import BaseImporter
from stargaze.commons import BoundingBox

_resources = importlib.resources.files('stargaze.resources')

with open(_resources / 'opentopo_api.toml', 'rb') as open_topo_file:
    _base_params = tomllib.load(open_topo_file)

load_dotenv()
_base_params["API_Key"] = os.environ["OpenTopo_API_Key"]

def to_params(box: BoundingBox) -> dict:
    """Get the specific parameters required by the OpenTopo API"""
    return {
        "south": box.minlat,
        "north": box.maxlat,
        "west": box.minlon,
        "east": box.maxlon
    }


class ReliefImporter(BaseImporter):
    """Importing relief data from OpenTopography"""

    _endpoint = 'https://portal.opentopography.org/API/globaldem'

    _table  = 'stargaze.relief'
    _column = 'rast'

    def fetch(self, bounds):
        """
        Sends request to the endpoint and returns the response as bytestream.

        This function sends a request parametrized with the BoundingBox
        coordinates and name of the global dataset defined as SRTMGL1, with
        30-meter precision, to the OpenTopography endpoint for accessing global
        datasets. The response body contains the raster file, in GeoTiff format
        by default.
        """
        params = to_params(bounds)
        params.update(_base_params)
        response = requests.get(self._endpoint, params=params, stream=True)
        response.raise_for_status()
        return response.content

    def transform(self, raster_binary):
        """
        Transforms the binary image into sql statements

        This function takes the GTiff image binary, puts into a temporary file
        and creates an SQL file with insertion statement, returning it in the
        standard output of the completed process.
        """
        with tempfile.NamedTemporaryFile(suffix='.tif') as tmp:
            tmp.write(raster_binary)
            tmp.flush()
            raster2pgsql_cmd = ["raster2pgsql", "-f", self._column, "-a", tmp.name,
                                self._table]
            sql_result = subprocess.run(raster2pgsql_cmd,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.DEVNULL,
                                        text=True)
        return sql_result

    def load(self, sql_result, session):
        with session.cursor() as cursor:
            cursor.execute(sql_result.stdout)


def main():
    relief_importer = ReliefImporter()
    bounds = BoundingBox(minlat=49.0, minlon=13.35, maxlat=50.1, maxlon=14.6)
    with open(_resources / 'credentials.toml', 'rb') as credentials_file:
        credentials = tomllib.load(credentials_file)
    with psycopg2.connect(**credentials) as session:
        relief_importer.run(bounds, session)


if __name__ == '__main__':
    main()
