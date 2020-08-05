#!/usr/bin/env python
import sys
import argparse
import logging
from .postfslint import ActionType, DupList
from . import rules
from itertools import filterfalse


def main(args=None):
    parser = argparse.ArgumentParser(description='')
    parser.add_argument("-f", "--fslint", help="fslint file to parse",
                        type=argparse.FileType('r'))
    parser.add_argument("-t", "--tsv", help="read tsv of duplicates with annotated actions",
                        type=argparse.FileType('r'))
    parser.add_argument("-s", "--suggest", help="apply suggestion rules",
                        action="store_true", default=False)
    parser.add_argument("-a", "--apply", help="apply actions",
                        action="store_true", default=False)
    parser.add_argument("-o", "--out", help="write tsv of duplicates with suggested actions",
                        type=argparse.FileType('w'))
    parser.add_argument("-K", "--nokeeps", help="Filter all-KEEP groups of duplicates",
                        action="store_true", default=False)
    parser.add_argument("-n", "--dryrun", help="with --apply, don't actually do anything but just print log statements",
                        action="store_true", default=False)
    parser.add_argument("-v", "--verbose", help="Long messages",
        dest="verbose", default=False, action="store_true")
    args = parser.parse_args(args)

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG if args.verbose else logging.INFO)

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
        duplist[:] = filterfalse(lambda g: all(a.type == ActionType.KEEP for a in g), duplist)

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
