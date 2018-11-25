#!/usr/bin/env python


#identify -verbose IMG_4573.JPG grep 'exif:DateTime'
#exiftool IMG_4573.JPG |grep -i date|sed -r 's/^[^:]*: ([0-9]{4}):([0-9][0-9]?):.*$/\1 \2/'|uniq

import subprocess, re, sys
import os, os.path
from os.path import join
import shutil
import logging
import fnmatch, re

photo_ext = set((".jpg",".jpeg",".gif",".cr2",".png"))

class PhotoSorter():
    def __init__(self,dry_run=False, verbose=False,recursive=True,blacklist=[".*"]):
        self.dry_run = dry_run
        self.recursive = recursive
        self.blacklist = blacklist

    def getEXIF(self,img):
        cmd = [ "exiftool", img ]
        output = subprocess.check_output(cmd)
        lines = output.split("\n")
        datere = re.compile("^([^:]*date[^:]*): ([0-9]{4}):([0-9][0-9]?):.*$",re.I)
        dates = set()
        for l in lines:
            if l.lower().find("date")>=0:
                match = datere.match(l)
                if match:
                    if match.group(1).strip() == "Create Date":
                        dates.add(match.groups()[1:3])
        return dates

    def sortphotos(self,src,dst):
        # get all regular files in src dir
        for dirpath, dirnames, filenames in os.walk(src):
            if not self.recursive:
                # don't recurse into subdirs
                del dirnames[:]
            # skip blacklisted files & dirs
            for pattern in self.blacklist:
                for i in xrange(len(dirnames)-1,-1,-1):
                    if fnmatch.fnmatch(dirnames[i], pattern):
                        logging.debug("Skipping blacklisted dir %s",dirnames[i])
                        del dirnames[i]
                for i in xrange(len(filenames)-1,-1,-1):
                    if fnmatch.fnmatch(filenames[i],pattern):
                        logging.debug("Skipping blacklisted file %s",filenames[i])
                        del filenames[i]
            # skip destination dirs
            dstyear = re.compile(join(dst,"[0-9]{4}/?"))
            month = re.compile("[0-9]{2}")
            if dstyear.match(dirpath):
                for i in xrange(len(dirnames)-1,-1,-1):
                    if month.match(dirnames[i]):
                        logging.debug("Skipping destination %s",join(dirpath,dirnames[i]))
                        del dirnames[i]

            # split extensions and group by base name
            filegroups = {}
            for f in filenames:
                base,ext = os.path.splitext(f)
                filegroups.setdefault(base,[]).append(ext)

            # filter groups with photos
            #filegroups = {base:exts for base,exts in filegroups.items() \
            #        if any([e.lower() in photo_ext for e in exts])}

            # Get list of photo dates for each group
            for base,exts in filegroups.items():
                dates = set()
                for ext in exts:
                    if ext.lower() in photo_ext:
                        dates.update( self.getEXIF(join(dirpath,base+ext)) )

                # move all files if we find a single date
                if len(dates) == 1:
                    date = dates.pop()
                    try:
                        self.movephoto(src,[join(os.path.relpath(dirpath,src),base+ext) for ext in exts],dst,date)
                    except OSError as e:
                        # duplicate. Log and continue
                        logging.error(str(e))
                else:
                    logging.warn("Multiple dates found for %s",",".join(join(dirpath,base+ext) for ext in exts))

    def movephoto(self,srcdir,imgs,dstdir,date):
        """Move a set of files atomically to a date-based destination.

        Move images from srcdir/img to destdir/YYYY/MM/img

        Args:
            srcdir (str):   source directory
            imgs (list):    list of paths relative to srcdir
            dstdir (str):   destination directory
            date (tuple):   tuple (year,month) as strings

        Exceptions:
            OSError: if any of the imgs already exist at the destination
        """
        year,month = date
        dst = join(dstdir,year,month)
        moves = [(join(srcdir,img),join(dst,img)) for img in imgs]
        # Move whole group together
        if not any(os.path.exists(dst) for src,dst in moves):
            for src,dst in moves:
                if not self.dry_run:
                    if not os.path.exists(os.path.dirname(dst)):
                        os.makedirs(os.path.dirname(dst))
                    shutil.move(src,dst)
                    logging.info( "mv \"{}\" \"{}\"".format(src,dst) )
                else:
                    print( "mv \"{}\" \"{}\"".format(src,dst) )
        else:
            raise OSError("File exists: %s"%[dst for src,dst in moves if os.path.exists(dst)][0])

