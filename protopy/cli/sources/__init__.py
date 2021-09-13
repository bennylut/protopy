from abc import abstractmethod
from contextlib import AbstractContextManager
from pathlib import Path



try:
    from typing import Protocol
except ImportError:
    from typing_extensions import Protocol


class Source(Protocol):
    @abstractmethod
    def use(self) -> "AbstractContextManager[Path]":
        ...

    @staticmethod
    def from_descriptor(descriptor: str) -> "Source":
        from protopy.cli.sources.git_source import GitSource
        from protopy.cli.sources.url_source import UrlSource
        from protopy.cli.sources.zip_source import ZipSource
        from protopy.cli.sources.file_system_source import FileSystemSource

        if descriptor.startswith("git+"):
            return GitSource(descriptor[5:])
        elif descriptor.startswith(("https://", "ssh://")) and descriptor.endswith(".git"):
            return GitSource(descriptor)
        elif descriptor.startswith(("http://", "https://")) and descriptor.endswith(".zip"):
            return UrlSource(descriptor, ZipSource)
        else:
            path = Path(descriptor)
            if not path.exists():
                raise FileNotFoundError(f"could not find template in {descriptor} or source not supported.")
            if path.is_dir():
                return FileSystemSource(path)
            elif path.suffix == "zip":
                return ZipSource(descriptor)
            else:
                raise ValueError(f"Unsupported File Type: {descriptor}")


