#!/usr/bin/env python
import sys
import click
import logging
from .postfslint import ActionType, DupList
from . import rules
from itertools import filterfalse


@click.command()
@click.option("-f", "--fslint", help="fslint file to parse", type=click.File("r"))
@click.option(
    "-t",
    "--tsv",
    help="read tsv of duplicates with annotated actions",
    type=click.File("r"),
)
@click.option(
    "-s", "--suggest", help="apply suggestion rules", is_flag=True, default=False
)
@click.option("-a", "--apply", help="apply actions", is_flag=True, default=False)
@click.option(
    "-o",
    "--out",
    help="write tsv of duplicates with suggested actions",
    type=click.File("w"),
)
@click.option(
    "-K",
    "--no-keeps",
    help="Filter all-KEEP groups of duplicates",
    is_flag=True,
    default=False,
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
def main(fslint, tsv, apply, out, no_keeps, dry_run, verbose):
    "Deal with duplicate images"

    logging.basicConfig(
        format="%(levelname)s: %(message)s",
        level=logging.DEBUG if args.verbose else logging.INFO,
    )

    # input
    if not (args.fslint or args.tsv):
        logging.error("No input specified")
        sys.exit(1)
    if args.fslint and args.tsv:
        logging.error("Expected exactly one input option")
        sys.exit(1)

    # Read input
    duplist = DupList(fslint=args.fslint, tsv=args.tsv)

    if args.suggest:
        # Apply rules
        duplist.annotate(rules.defaultrules)

    if args.nokeeps:
        # Filter out all=KEEP groups
        duplist[:] = filterfalse(
            lambda g: all(a.type == ActionType.KEEP for a in g), duplist
        )

    if args.apply:
        duplist.apply(args.dryrun)

    # Write output
    if args.out:
        try:
            duplist.write(args.out)
        except BrokenPipeError as ex:
            pass  # piping is fine
        except IOError as ex:
            logging.error(ex)
            sys.exit(1)


if __name__ == "__main__":
    main()
