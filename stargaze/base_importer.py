from abc import ABC, abstractmethod

from stargaze.commons import BoundingBox


class BaseImporter(ABC):

    @abstractmethod
    def fetch(self, bounds: BoundingBox):
        """Fetches raw data extract."""

    @abstractmethod
    def transform(self, extract):
        """Transforms raw data extract."""

    @abstractmethod
    def load(self, data):
        """Loads transformed data into the database."""

    def run(self, bounds: BoundingBox, session) -> None:
        """Executes the pipeline."""
        self.load(self.transform(self.fetch(bounds)), session)
