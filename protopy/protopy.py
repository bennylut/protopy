import zipfile
from pathlib import Path
from typing import Dict, List

import protopy.engine

from protopy.cli.sources import Source
from protopy.cli.utils.resources import resource

_NEW_TEMPLATE_RESOURCE = "templates/new_template.zip"


class Protopy:

    def __init__(self):
        self._engine = protopy.engine.ProtopyEngine()

    def render(self, descriptor: str, out_dir: Path, args: List[str], kwargs: Dict[str, str]):
        with Source.from_descriptor(descriptor).use() as template_path:
            self._engine.render(template_path, out_dir, args, kwargs)

    def create_template(self, path: Path):
        if path.exists() and not path.is_dir():
            raise ValueError(f"{path} is not a directory")
        elif not path.exists():
            path.mkdir(parents=True)

        with resource(_NEW_TEMPLATE_RESOURCE) as nt:
            zipfile.ZipFile(nt).extractall(path)

    @staticmethod
    def instance():
        return _instance


_instance = Protopy()
