# kamaji
Tool for organizing and renaming photos and files.

- deduplication
- sorting

## Installation

### Prerequisites

Kamaji requires python 3.6.

Sorting by EXIF tags requirex `exiftool` to be installed.

Deduplication parses output from `fslint`.

    sudo apt-get install exiftool fslint

As of 2020, `fslint` has not been updated for python 3, so it may need to be run in a
separate environment.

### Installing from source

Next, install the package:

    python setup.py install

## Running

It can then be run as a python module:

    python -m kamaji.sort -h
    python -m kamaji.uniq -h


## Examples

Parse output of fslint or findup into a TSV file. Don't list groups of duplicates
if they all pass 'KEEP' rules.

    python -m kamaji.uniq -f duplicates.fsdup -s -o duplicates.tsv -K

This TSV file can be checked over and edited if needed. Then, to apply changes:

    python -m kamaji.uniq -a -t duplicates.tsv


## License

Code is released under the GNU General Public License version 3.0 or later.
