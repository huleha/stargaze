import importlib
import psycopg2
import psycopg2.extras
import requests
import subprocess
import tempfile
import tomllib

from stargaze.base_importer import BaseImporter
from stargaze.commons import BoundingBox

_resources = importlib.resources.files('stargaze.resources')


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

    _raster_table = 'stargaze.relief'

    with open(_resources / 'opentopo_api.toml', 'rb') as open_topo_file:
        _base_params = tomllib.load(open_topo_file)

    def fetch(self, bounds):
        """
        Sends request to the endpoint and returns the response as bytestream.

        This function sends a request parametrized with the BoundingBox coordinates
        and name of the global dataset defined as SRTMGL1, with 30-meter precision,
        to the OpenTopography endpoint for accessing global datasets.
        The response body contains the raster file, in GeoTiff format by default.
        """
        params = to_params(bounds)
        params.update(self._base_params)
        response = requests.get(self._endpoint, params=params, stream=True)
        response.raise_for_status()
        tmp = tempfile.NamedTemporaryFile(suffix='.tif')
        tmp.write(response.content)
        tmp.flush()
        return tmp
        # print(f"Downloaded file size: {len(response.content)} bytes")
        # return response.content

    def transform(self, tmp_raster):
        """
        Transforms the raster image into sql statements

        This function takes the GTiff image temporary file and creates an SQL file
        with insertion statement, returning it in the standard output of the
        completed process.
        """
        print("Temporary file's name is ", tmp_raster.name)
        raster2pgsql_cmd = ["raster2pgsql", "-I", "-a", tmp_raster.name,
                            self._raster_table]
        sql_result = subprocess.run(raster2pgsql_cmd, stdout=subprocess.PIPE,
                                    text=True)
        tmp_raster.close()
        return sql_result

    def load(self, sql_result, session):
        with session.cursor() as cursor:
            cursor.execute(sql_result.stdout)


def main():
    relief_importer = ReliefImporter()
    bounds = BoundingBox(minlat=50.0, minlon=14.35, maxlat=50.1, maxlon=14.6)
    with open(_resources / 'credentials.toml', 'rb') as credentials_file:
        credentials = tomllib.load(credentials_file)
    with psycopg2.connect(**credentials) as session:
        relief_importer.run(bounds, session)


if __name__ == '__main__':
    main()
