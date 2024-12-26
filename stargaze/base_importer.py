from abc import ABC, abstractmethod

from stargaze.commons import BoundingBox


class BaseImporter(ABC):

    @abstractmethod
    def fetch(self, bounds: BoundingBox):
        """Fetch data."""

    @abstractmethod
    def transform(self, extract):
        """Transforms raw data."""

    @abstractmethod
    def load(self, data):
        """Loads data into the database."""

    def run(self, bounds: BoundingBox) -> None:
        """Executes the pipeline."""
        self.load(self.transform(self.fetch(bounds)))
