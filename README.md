postfslint
----------

Post-processing of [fslint](https://github.com/pixelb/fslint) files.

https://github.com/sbliven/postfslint


Installing
----------

    python setup.py install


Examples
--------

Parse output of fslint or findup into a TSV file. Don't list groups of duplicates
if they all pass 'KEEP' rules.

    python -m postfslint -f duplicates.fsdup -s -o duplicates.tsv -K

This TSV file can be checked over and edited if needed. Then, to apply changes:

    python -m postfslint -a -t duplicates.tsv


License
-------

Code is released under the GNU General Public License version 3.0 or later.
