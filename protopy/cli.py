from cleo.application import Application

from protopy.commands.generate_command import GenerateCommand
from protopy.commands.new_command import NewCommand

application = Application()
application.add(NewCommand())
application.add(GenerateCommand())


def main():
    application.run()


if __name__ == '__main__':
    main()
