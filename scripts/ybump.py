#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  ybump.py
#
#  Copyright 2015 Ikey Doherty <ikey@solus-project.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
from ypkg import sanity


import sys
import yaml
import os


def usage(msg=None, ex=1):
    if msg:
        print msg
    else:
        print "Usage: %s" % sys.argv[0]
    sys.exit(ex)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        usage()

    ymlfile = sys.argv[1]
    if not os.path.exists(ymlfile):
        usage("Specified file does not exist")
    if not ymlfile.endswith(".yml"):
        usage("%s does not look like a valid package.yml file")

    if not sanity.sane(ymlfile):
        print "File does not appear to be valid, aborting"
        sys.exit(1)

    buf = list()
    with open(ymlfile, "r") as infile:
        for line in infile.readlines():
            line = line.replace("\n", "").replace("\r", "")
            if ":" in line:
                spl = line.split(":")
                if len(spl) != 2:
                    buf.append(line)
                    continue
                name = spl[0].strip()
                if name == "release":
                    val = int(spl[1].strip()) + 1
                    buf.append("%s: %s" % (spl[0], val))
                else:
                    buf.append(line)
            else:
                buf.append(line)
    try:
        f = open(ymlfile, "w")
        f.writelines(["%s\n" % x for x in buf])
        f.close()
    except Exception as e:
        print "Error writing file, may need to reset it."
        print e
        sys.exit(1)
