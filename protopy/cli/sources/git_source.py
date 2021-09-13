from contextlib import contextmanager
from pathlib import Path

import pygit2
from tempfile import TemporaryDirectory

from protopy.cli.sources import Source


class GitSource(Source):

    def __init__(self, repo_url: str):
        self._repo_url = repo_url

    @contextmanager
    def use(self):
        with TemporaryDirectory() as temp_dir:
            pygit2.clone_repository(self._repo_url, temp_dir)
            yield Path(temp_dir)
