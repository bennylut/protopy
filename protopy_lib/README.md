# Protopy Lib

A library for rendering directory trees. allows for embedding into other applications with minimal dependencies

Usage and additional documentation can be found in [Protopy's Git Repo](https://github.com/bennylut/protopy)

The Protopy library (protopy_lib) includes the Protopy engine itself without the commandline and support for multiple
template sources. It has minimal set of dependencies and is intended for embedding inside other applications.

it exposes the following class:

```python

class ProtopyEngine:
    def render_doc(self, template_dir: Union[Path, str], template_descriptor: Optional[str] = None,
                   command_prefix: str = "protopy") -> str:
        """
        :param the directory holding the template
        :param template_descriptor: the descriptor that used to resolve the template directory, if not provided,
                                    the template directory will be considered as the descriptor
        :param command_prefix: the prefix of the commandline that should be used to generate this template
        :return: a generated documentation for this template
        """

    def render(self, template_dir: Union[Path, str], target_dir: Union[Path, str],
               args: List[str], kwargs: Dict[str, str], extra_context: Dict, *,
               excluded_files: Optional[List[Path]] = None, allow_overwrite: bool = False):
        """
        renders the given template into the target directory

        :param template_dir: the directory holding the template
        :param target_dir: the directory to output the generated content into
        :param args: positional arguments for the template
        :param kwargs: named arguments for the template
        :param extra_context: extra variables that will be available inside proto.py
        :param excluded_files:  list of path objects that represents files in the template directory that should be
                                excluded from the generation process
        :param allow_overwrite: if True, files that are already exists will be overridden by the template
        """
```
