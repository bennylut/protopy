import os
from pathlib import Path

from cleo.commands.command import Command

from protopy.protopy import Protopy


class NewCommand(Command):
    """
    create new template (and populate it with some example content)

    new
        {out_dir? : directory to create the template in, defaults to the current directory}
    """

    def handle(self) -> int:
        path = self.argument("out_dir")
        if not path:
            path = os.getcwd()

        Protopy.instance().create_template(Path(path))
        return 0
