import os
from typing import List

from cleo.commands.command import Command

from protopy.protopy import Protopy


class ManCommand(Command):
    """
    print information about a template

    man
        {template : the template to examine (supports path, git, zip, url to zip)}
    """

    def handle(self) -> int:
        template_descriptor = self.argument("template")
        self.io.write(Protopy.instance().manual(template_descriptor), new_line=True)
        return 0
