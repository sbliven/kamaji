import click
import logging
from .sort import PhotoSorter


@click.command()
@click.argument(
    "src",
    # help="Source directory for images",
    type=click.Path(exists=True, file_okay=False),
)
@click.argument(
    "dst",
    # help="Destination directory for images. Default:src",
    default=None,
    type=click.Path(file_okay=False),
)
@click.option(
    "-r",
    "--recursive",
    is_flag=True,
    default=False,
    help="Recurse into subdirectories, preserving the input directory structure while splitting by date",
)
@click.option(
    "-n",
    "--dry-run",
    is_flag=True,
    default=False,
    help="Do not actually perform file moves",
)
@click.option("-v", "--verbose", is_flag=True, help="Verbose logging")
@click.help_option("-h", "--help")
def main(src, dst, recursive, dry_run, verbose):
    "Sort images by year and month"

    log_level = logging.DEBUG if verbose else logging.WARN
    logging.basicConfig(level=log_level)  # , format="%(message)s")

    sorter = PhotoSorter(recursive=recursive, dry_run=dry_run)
    sorter.sortphotos(src, dst)


if __name__ == "__main__":
    main()
