import importlib.util
import shutil
from pathlib import Path
from types import ModuleType
from typing import Union, Set, Optional, List, Any, Dict

import sys
from cleo.io.inputs.argv_input import ArgvInput
from cleo.io.io import IO
from cleo.io.outputs.stream_output import StreamOutput
from cleo.ui.choice_question import ChoiceQuestion
from cleo.ui.confirmation_question import ConfirmationQuestion
from cleo.ui.question import Question
from jinja2 import FileSystemLoader
from jinja2.sandbox import SandboxedEnvironment
from distutils.dir_util import copy_tree


class ProtopyEngine:

    def __init__(self, io: Optional[IO] = None):
        if io:
            self._io = io
        else:
            input = ArgvInput()
            input.set_stream(sys.stdin)
            self._io = io or IO(input, StreamOutput(sys.stdout), StreamOutput(sys.stderr))
        self._jinja = SandboxedEnvironment(loader=FileSystemLoader("/"))

    def render_doc(
            self, template_dir: Union[Path, str],
            template_descriptor: Optional[str] = None,
            command_prefix: str = "protopy") -> str:

        """
        :param the directory holding the template
        :param template_descriptor: the descriptor that used to resolve the template directory, if not provided,
                                    the template directory will be considered as the descriptor
        :param command_prefix: the prefix of the commandline that should be used to generate this template
        :return: a generated documentation for this template
        """

        import protopy.doc_generator as dg
        return dg.generate(Path(template_dir), template_descriptor, command_prefix)

    def render(self, template_dir: Union[Path, str], target_dir: Union[Path, str],
               args: List[str], kwargs: Dict[str, str], extra_context: Dict[str, Any], *,
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

        template_dir = (template_dir if isinstance(template_dir, Path) else Path(template_dir)).absolute()
        target_dir = (target_dir if isinstance(target_dir, Path) else Path(target_dir)).absolute()
        excluded_files = [*(excluded_files or []), template_dir / "proto.py", template_dir / "__pycache__"]

        target_dir.mkdir(exist_ok=True)

        ui = _UserInteractor(self._io, args, kwargs)
        module = self._load_proto(template_dir.joinpath("proto.py"), ui,
                                  {**extra_context, "args": args, "kwargs": kwargs})

        context = {k: v for k, v in vars(module).items() if not k.startswith("_")}

        ignored_files = set(self._load_ignored_files_list(template_dir))
        ignored_files.update(p.absolute() for p in excluded_files)

        if not allow_overwrite:
            self._check_override(template_dir, target_dir, context, ignored_files)

        self._render(template_dir, target_dir, context, ignored_files)

        if hasattr(module, "post_generation") and callable(module.post_generation):
            module.post_generation()

    def _check_override(self, template_dir: Path, target_dir: Path, context: dict, ignored_files: Set[Path]):

        jinja = self._jinja

        for template_child in template_dir.iterdir():
            if template_child in ignored_files:
                continue

            name = jinja.from_string(template_child.name).render(context)

            if not name:  # empty names indicate unneeded files
                continue

            target_child = (target_dir / name).resolve()

            if not target_child.parent.exists():
                return

            if template_child.is_dir():
                if template_child.exists():
                    self._check_override(template_child, target_child, context, ignored_files)
            else:
                if target_child.suffix == '.tmpl':
                    target_child = target_child.with_suffix('')

                if target_child.exists():
                    raise IOError(f"file already exists: {target_child}")

    def _render(self, template_dir: Path, target_dir: Path, context: dict, ignored_files: Set[Path]):

        jinja = self._jinja

        for template_child in template_dir.iterdir():
            if template_child in ignored_files:
                continue

            name = jinja.from_string(template_child.name).render(context)

            if not name:  # empty names indicate unneeded files
                continue

            target_child = (target_dir / name).resolve()

            if not target_child.parent.exists():
                target_child.parent.mkdir(parents=True)

            if template_child.is_dir():
                if (template_child / ".protopypreserve").exists():
                    copy_tree(str(template_child.absolute()), str(target_child.absolute()))
                    return

                target_child.mkdir(exist_ok=True)
                self._render(template_child, target_child, context, ignored_files)
            elif target_child.suffix == ".tmpl":
                with target_child.with_suffix("").open("w") as f:
                    jinja.get_template(str(template_child)).stream(context).dump(f)
            else:
                shutil.copy(template_child, target_child)

    def _load_ignored_files_list(self, template_root: Path):
        result = []
        pi_file = template_root.joinpath(".protopyignore")

        if pi_file.exists():
            lines = pi_file.read_text().splitlines()
            result = [f.absolute() for line in lines if line.strip() for f in template_root.glob(line)]

        for sub_dir in template_root.iterdir():
            if sub_dir.is_dir():
                result.extend(self._load_ignored_files_list(sub_dir))

        return result

    def _load_proto(self, proto_file: Path, ui: "_UserInteractor", context: dict):
        try:
            spec = importlib.util.spec_from_file_location("__PROTO__", proto_file)
            module = importlib.util.module_from_spec(spec)

            ui.install(module)
            for k, v in context.items():
                setattr(module, k, v)

            spec.loader.exec_module(module)
            return module
        except Exception as e:
            raise RuntimeError(f"Error while evaluating: {proto_file}") from e


class _UserInteractor:
    def __init__(self, io: IO, args: list, kwargs: dict):
        self._args = args or []
        self._kwargs = kwargs
        self._io = io

    def _pre_answered(self, named_arg: str, positional_arg: int) -> Optional[str]:
        if named_arg in self._kwargs:
            return self._kwargs[named_arg]

        if 0 <= positional_arg < len(self._args):
            return self._args[positional_arg]

        return None

    def say(self, msg: str):
        """
        display a message to the user
        :param msg: the message to display
        """
        self._io.write_line(msg)

    def confirm(
            self, named_arg: str, *, prompt: str, doc: str = "", default: bool = True, positional_arg: int = -1) -> bool:

        """
        ask the user for yes/no confirmation (either retrieving it from the command line or from the user supplied arguments)
        :param named_arg: the name of the argument that may contain the value for this function to return (supports the values y,yes,n,no)
        :param prompt: (optional - defaults to a string generated from named_arg) the prompt to show to the user
        :param default: (optional - defaults to True = 'yes') the default value to suggest the user
        :param positional_arg: (optional - defaults to -1) the index of the positional argument that may contain the
                                value for this function to return
        :param doc: documentation to show in the commandline (must be a string literal)
        :return: True if the user confirmed or False otherwise
        """

        pre_answered = self._pre_answered(named_arg, positional_arg)
        if pre_answered:
            return pre_answered.lower() in ('y', 'yes', 'true')

        q = ConfirmationQuestion(prompt, default)
        r = q.ask(self._io)
        return r if isinstance(r, bool) else r.lower() in ('y', 'yes')

    def arg(self, named_arg: str, *, doc: str = "", default: str = "", positional_arg=-1):
        """
        fetch a value from the commandline arguments, without asking the user for it if not provided
        :param named_arg: the name of the argument that may contain the value for this function to return (supports the values y,yes,n,no)
        :param doc: documentation to show in the commandline (must be a string literal)
        :param default: (optional - defaults to None) the default value to suggest the user
        :param positional_arg:  (optional - defaults to -1) the index of the positional argument that may contain the
                                value for this function to return
        :return: the requested user value
        """
        pre_answered = self._pre_answered(named_arg, positional_arg)
        return pre_answered if pre_answered is not None else default

    def ask(self, named_arg: str, *, prompt: str = None, default: Any = "", choices: Optional[List[str]] = None,
            autocomplete: Optional[List[str]] = None, secret: bool = False, positional_arg: int = -1,
            doc: str = ""):

        """
        ask the user for information (either retrieving it from the command line or from the user supplied arguments)
        :param named_arg: the name of the argument that may contain the value for this function to return
        :param prompt: (optional - defaults to a string generated from named_arg) the prompt to show to the user
        :param default: (optional - defaults to None) the default value to suggest the user
        :param choices: (optional - defaults to None) list of choices to restrict the user input to
        :param autocomplete: (optional - defaults to None) list of autocomplete suggestions to help the user with
        :param secret: (optional - defaults to False) set to True to hide the user input
        :param positional_arg:  (optional - defaults to -1) the index of the positional argument that may contain the
                                value for this function to return
        :param doc: documentation to show in the commandline (must be a string literal)

        :return: the requested user input
        """

        if not prompt:
            prompt = named_arg.replace("_", " ").title()

        pre_answered = self._pre_answered(named_arg, positional_arg)
        if pre_answered:
            return pre_answered

        if choices:
            q = ChoiceQuestion(prompt, choices, default or 0)
        else:
            if default:
                prompt = f"{prompt} [{default}] >"
            else:
                prompt = f"{prompt} >"

            q = Question(prompt, default)

        if autocomplete:
            q.set_autocomplete_values(autocomplete)
        if secret:
            q.hide(True)

        return q.ask(self._io)

    def install(self, module: ModuleType):
        module.ask = self.ask
        module.confirm = self.confirm
        module.say = self.say
        module.arg = self.arg


if __name__ == '__main__':
    e = ProtopyEngine()
    shutil.rmtree("/home/bennyl/projects/tests/cookie2")
    e.render("/home/bennyl/projects/relaxed-poetry/poetry/resources/new_project_template",
             "/home/bennyl/projects/tests/cookie2", ['blu'], {'author': "bli"})
