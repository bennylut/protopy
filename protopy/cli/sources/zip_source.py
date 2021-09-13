from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from protopy.cli.sources import Source


class ZipSource(Source):

    def __init__(self, zip_file_path: str):
        self._zip_file_path = Path(zip_file_path)

    @contextmanager
    def use(self) -> Path:
        with TemporaryDirectory() as temp_dir:
            with open(self._zip_file_path) as f:
                ZipFile(f).extractall(temp_dir)
            yield temp_dir

