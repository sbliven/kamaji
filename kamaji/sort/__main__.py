import argparse
import logging
from .sort import PhotoSorter


def main(argv=None):
    parser = argparse.ArgumentParser(description="Sort images by year and month")
    parser.add_argument("src", metavar="src", help="Source directory for images")
    parser.add_argument(
        "dst",
        metavar="dst",
        default=None,
        help="Destination directory for images. Default:src",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        default=False,
        action="store_true",
        help="Recurse into subdirectories, preserving the input directory structure while splitting by date",
    )
    parser.add_argument(
        "-y",
        "--dry-run",
        default=False,
        action="store_true",
        help="Do not actually perform file moves",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        default=logging.WARN,
        action="store_const",
        dest="logLevel",
        const=logging.DEBUG,
    )

    args = parser.parse_args(argv)

    logging.basicConfig(level=args.logLevel)  # , format="%(message)s")

    sorter = PhotoSorter(recursive=args.recursive, dry_run=args.dry_run)
    sorter.sortphotos(args.src, args.dst)


if __name__ == "__main__":
    main()
