import os
from typing import List

from cleo.commands.command import Command

from protopy.protopy import Protopy


class GenerateCommand(Command):
    """
    generate directory tree based on a given template

    generate
        {template : the template to use (supports path, git, zip, url to zip, global template ref (with #))}
        {output_path : where to put the generated content }
        {template_args?* : template arguments, can be positional and key=value}
    """

    def handle(self) -> int:
        template_descriptor = self.argument("template")
        out_path = self.argument("output_path")
        if not out_path:
            out_path = os.getcwd()

        template_args: List[str] = self.argument("template_args")
        args = []
        kwargs = {}

        for arg in template_args:
            try:
                key,value = arg.split("=",2)
            except ValueError:
                key, value = (None, arg)

            if key:
                kwargs[key] = value
            else:
                args.append(value)

        Protopy.instance().render(template_descriptor, out_path, args, kwargs)
        return 0
