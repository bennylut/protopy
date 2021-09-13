from contextlib import contextmanager
from pathlib import Path

from protopy.cli.sources import Source


class FileSystemSource(Source):

    def __init__(self, path: Path):
        self._path = path

    @contextmanager
    def use(self):
        yield self._path
