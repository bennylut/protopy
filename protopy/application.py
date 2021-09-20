from cleo.application import Application

from protopy.cli.commands.generate_command import GenerateCommand
from protopy.cli.commands.man_command import ManCommand
from protopy.cli.commands.new_command import NewCommand

application = Application()
application.add(NewCommand())
application.add(GenerateCommand())
application.add(ManCommand())


def main():
    application.run()


if __name__ == '__main__':
    main()
