import click

from .sort.__main__ import main as sort
from .uniq.__main__ import main as uniq


@click.group()
@click.help_option("-h", "--help")
def main():
    pass


@click.command()
def uniq():
    pass


main.add_command(sort, "sort")
main.add_command(uniq, "uniq")

if __name__ == "__main__":
    main()
