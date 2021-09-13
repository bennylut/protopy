from contextlib import contextmanager
from types import ModuleType
from typing import cast

try:
    import importlib.resources as pkg_resources
except ImportError:
    import importlib_resources as pkg_resources

import protopy.cli.resources as resources



@contextmanager
def resource(path: str):

    with pkg_resources.path(cast(ModuleType, resources), "") as resources_file:
        yield resources_file / path
