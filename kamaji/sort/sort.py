#!/usr/bin/env python


# identify -verbose IMG_4573.JPG grep 'exif:DateTime'
# exiftool IMG_4573.JPG |grep -i date|sed -r 's/^[^:]*: ([0-9]{4}):([0-9][0-9]?):.*$/\1 \2/'|uniq

import subprocess, re, sys
import os, os.path
from os.path import join
import shutil
import logging
import fnmatch, re
from typing import Iterable, Tuple, List, Dict, Set

photo_ext = set((".jpg", ".jpeg", ".gif", ".cr2", ".png"))

EXIFTOOL = os.environ.get("EXIFTOOL", "exiftool")


class PhotoSorter:
    """Sorts photos into dated folders (`YYYY/MM/img`)

    Dates are based on file creation date and EXIF data. If several conflicting dates
    are found, sorting aborts.

    """

    def __init__(self, dry_run=False, recursive=True, blacklist=[".*"]):
        """Create a new PhotoSorter

        Args:
        - dry_run: don't actually move the files, just log what actions would be performed
        - recursive: descend into subdirectories
        - blacklist: a list of file globs to ignore. Defaults to ".*" to ignore
          hidden files
        """
        self.dry_run = dry_run
        self.recursive = recursive
        self.blacklist = blacklist

    def getEXIF(self, img: str) -> Iterable[Tuple[str, str]]:
        """Get the creation date for an image from EXIF tags

        Requires `exiftool` to be installed.

        Parses 'Create Date' tags

        Args:
        - img: image filename

        Returns:
        - A list of (year, month) tuples

        Raises:
        - CalledProcessError: error running exiftool
        """
        cmd = [EXIFTOOL, img]
        output = subprocess.check_output(cmd, universal_newlines=True)
        lines = output.split("\n")
        datere = re.compile("^([^:]*date[^:]*): ([0-9]{4}):([0-9][0-9]?):.*$", re.I)
        dates: Set[Tuple[str, str]] = set()
        for l in lines:
            if l.lower().find("date") >= 0:
                match = datere.match(l)
                if match:
                    if match.group(1).strip() == "Create Date":
                        dates.add((match.group(2), match.group(3)))
        return dates

    def sortphotos(self, src: str, dst: str):
        """Sort Photos

        Iterates through all files within src and tries to identify the creation date.
        This is done by inspecting file timestamp and EXIF tags.

        If several files are found in each directory differing only by extension
        (e.g. a JPG and RAW), they are grouped together.

        If the unique year/month for a file (and any grouped files) cannot be
        determined, files are left in src.

        Args:
        - src: source directory
        - dst: destination directory
        """
        # get all regular files in src dir
        for dirpath, dirnames, filenames in os.walk(src):
            if not self.recursive:
                # don't recurse into subdirs
                del dirnames[:]
            # skip blacklisted files & dirs
            for pattern in self.blacklist:
                for i in range(len(dirnames) - 1, -1, -1):
                    if fnmatch.fnmatch(dirnames[i], pattern):
                        logging.debug("Skipping blacklisted dir %s", dirnames[i])
                        del dirnames[i]
                for i in range(len(filenames) - 1, -1, -1):
                    if fnmatch.fnmatch(filenames[i], pattern):
                        logging.debug("Skipping blacklisted file %s", filenames[i])
                        del filenames[i]
            # skip destination dirs
            dstyear = re.compile(join(dst, "[0-9]{4}/?"))
            month = re.compile("[0-9]{2}")
            if dstyear.match(dirpath):
                for i in range(len(dirnames) - 1, -1, -1):
                    if month.match(dirnames[i]):
                        logging.debug(
                            "Skipping destination %s", join(dirpath, dirnames[i])
                        )
                        del dirnames[i]

            # split extensions and group by base name
            filegroups: Dict[str, List[str]] = {}
            for f in filenames:
                base, ext = os.path.splitext(f)
                filegroups.setdefault(base, []).append(ext)

            # filter groups with photos
            # filegroups = {base:exts for base,exts in filegroups.items() \
            #        if any([e.lower() in photo_ext for e in exts])}

            # Get list of photo dates for each group
            for base, exts in filegroups.items():
                dates: Set[Tuple[str, str]] = set()
                for ext in exts:
                    if ext.lower() in photo_ext:
                        dates.update(self.getEXIF(join(dirpath, base + ext)))

                # move all files if we find a single date
                if len(dates) == 1:
                    date = dates.pop()
                    try:
                        self.movephoto(
                            src,
                            [
                                join(os.path.relpath(dirpath, src), base + ext)
                                for ext in exts
                            ],
                            dst,
                            date,
                        )
                    except OSError as e:
                        # duplicate. Log and continue
                        logging.error(str(e))
                else:
                    logging.warn(
                        "Multiple dates found for %s",
                        ",".join(join(dirpath, base + ext) for ext in exts),
                    )

    def movephoto(
        self, srcdir: str, imgs: Iterable[str], dstdir, date: Tuple[str, str]
    ):
        """Move a set of files atomically to a date-based destination.

        Move images from srcdir/img to destdir/YYYY/MM/img

        Args:
            srcdir: source directory
            imgs: list of paths relative to srcdir
            dstdir: destination directory
            date: tuple (year,month) as strings

        Exceptions:
            OSError: if any of the imgs already exist at the destination
        """
        year, month = date
        dst = join(dstdir, year, month)
        moves = [(join(srcdir, img), join(dst, img)) for img in imgs]
        # Move whole group together
        if not any(os.path.exists(dst) for src, dst in moves):
            for src, dst in moves:
                if not self.dry_run:
                    if not os.path.exists(os.path.dirname(dst)):
                        os.makedirs(os.path.dirname(dst))
                    shutil.move(src, dst)
                    logging.info('mv "{}" "{}"'.format(src, dst))
                else:
                    print('mv "{}" "{}"'.format(src, dst))
        else:
            raise OSError(
                "File exists: %s"
                % [dst for src, dst in moves if os.path.exists(dst)][0]
            )
