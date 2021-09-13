import functools
import shutil
from contextlib import contextmanager
from tempfile import TemporaryFile
from typing import Callable

from protopy.cli.sources import Source
import requests


class UrlSource(Source):
    def __init__(self, url: str, sub_source: Callable[[str], Source]):
        self._url = url
        self._sub_source = sub_source

    @contextmanager
    def use(self):
        with TemporaryFile() as temp_file:
            with requests.get(self._url, stream=True) as r:
                r.raise_for_status()
                r.raw.read = functools.partial(r.raw.read, decode_content=True)
                with open(temp_file, "wb") as f:
                    shutil.copyfileobj(r.raw, f)

            with self._sub_source(temp_file).use() as result:
                yield result
