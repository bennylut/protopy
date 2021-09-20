import ast
from numbers import Number
from pathlib import Path
from typing import Any, List, Optional


def generate(protopy_module_path: Path, template_descriptor: Optional[str] = None,
             command_prefix: str = "protopy") -> str:
    if not template_descriptor:
        template_descriptor = str(protopy_module_path.parent)

    source = protopy_module_path.read_text()
    source_tree: ast.Module = compile(source, "proto.py", "exec", ast.PyCF_ONLY_AST)

    doc = "Description:\n  "

    # extracting the doc string and creating the description section
    first_expr = next((expr for expr in source_tree.body if isinstance(expr, ast.Expr)), None)
    doc_str = 'Not Given.'
    if first_expr and isinstance(first_expr.value, ast.Str):
        doc_str = first_expr.value.s.strip()

    doc += "  ".join(doc_str.splitlines())

    # extracting the arguments
    visitor = _ArgsVisitor()
    visitor.visit(source_tree)

    # creating the usage section
    positional_args = sorted((it for it in visitor.args if it.position is not None), key=lambda it: it.position)
    usage = f"{command_prefix} {template_descriptor} "
    depth = 0
    for i, pa in enumerate(positional_args):
        if i != pa.position:
            break
        if depth > 0:
            usage += " "
        usage += f"[<{pa.arg_name}>"
        depth += 1

    if depth > 0:
        usage += "]" * depth + " "

    usage += "[<argument=value>...]"

    doc += f"\n\nUsage:\n  {usage}"

    # creating the arguments section
    doc += f"\n\nArguments:"
    max_len = max(len(a.arg_name) for a in visitor.args)
    for arg in visitor.args:
        doc += f"\n  {arg.doc(max_len)}"

    return doc


class _ArgDoc:
    def __init__(self, arg_name: str, default_value: Any, prompt: str, choices: Optional[List[str]],
                 position: Optional[int]):
        self.arg_name = arg_name
        self.default_value = default_value
        self.prompt = prompt
        self.choices = choices
        self.position = position

    def doc(self, width: Optional[int] = None):
        if width is None:
            width = len(self.arg_name)

        doc = f"{self.arg_name :<{width}} - {self.prompt}"
        if self.choices:
            doc += f", can be any of: {self.choices}"
        if self.default_value:
            doc += f", defaults to '{self.default_value}'"

        doc += "."

        return doc


def _materialize(value) -> Any:
    if isinstance(value, ast.Str):
        return value.s
    elif isinstance(value, ast.Num):
        return value.n
    elif isinstance(value, ast.List):
        result = [_materialize(v) for v in value.elts]
        return result if all(result) else None

    return None


def _keyword_value(call: ast.Call, keyword: str) -> Any:
    value = next((kw.value for kw in call.keywords if kw.arg == keyword), None)
    if not value:
        return None

    return _materialize(value)


class _ArgsVisitor(ast.NodeVisitor):

    def __init__(self):
        self.args: List[_ArgDoc] = []
        self.arg_names = set()

    def visit_Call(self, node: ast.Call) -> Any:
        func = node.func.id if hasattr(node.func, "id") else ""

        if func in ("ask", "confirm", "arg"):

            try:
                arg_name = _materialize(node.args[0])
            except:
                arg_name = _keyword_value(node, 'named_arg')

            if not arg_name or arg_name in self.arg_names:
                return

            self.arg_names.add(arg_name)

            prompt = _keyword_value(node, "doc") or _keyword_value(node, 'prompt')
            if not prompt:
                prompt = arg_name.replace("_", " ").title()
            choices: Optional[List[str]] = _keyword_value(node, 'choices') if func != 'confirm' else ['true', 'false']

            default_value: Any = _keyword_value(node, 'default')
            if func == 'confirm' and not default_value:
                default_value = "true"

            if choices and isinstance(default_value, int):
                default_value = choices[default_value]

            positional_arg = _keyword_value(node, 'positional_arg')
            positional_arg = positional_arg if isinstance(positional_arg, int) else None

            self.args.append(_ArgDoc(arg_name, default_value, prompt, choices, positional_arg))
