#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  yupdate.py
#  
#  Copyright 2015 Ikey Doherty <ikey@solus-project.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
import sys
import yaml
import os
import commands
import pisi.version

import sys
sys.path.append("/usr/share/ypkg")
import sanity

from sanity import TarSource

def usage(msg=None, ex=1):
    if msg:
        print msg
    else:
        print "Usage: %s" % sys.argv[0]
    sys.exit(ex)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        usage()

    ymlfile = "package.yml"
    if not os.path.exists(ymlfile):
        usage("Specified file does not exist")
    if not ymlfile.endswith(".yml"):
        usage("%s does not look like a valid package.yml file")

    if not sanity.sane(ymlfile, checkall=False):
        print "File does not appear to be valid, aborting"
        sys.exit(1)

    newversion = sys.argv[1]
    try:
        d = pisi.version.Version(newversion)
    except Exception, e:
        print("Problematic version string: %s" % e)
        sys.exit(1)

    url = sys.argv[2]
    file = url.split("/")[-1]

    try:
        r = os.system("wget \"%s\"" % url)
    except:
        print "Failed to download file"
        sys.exit(1)
    if r != 0:
        print "Failed to download file"
        sys.exit(1)

    sha256 = commands.getoutput("sha256sum %s" % file).split()[0].strip()

    bufTop = list()
    bufEnd = list()

    hitSources = False
    with open(ymlfile, "r") as infile:
        for line in infile.readlines():
            buf = bufEnd if hitSources else bufTop
            line = line.replace("\n","").replace("\r","")
            if ":" in line:
                spl = line.split(":")
                if len(spl) != 2:
                    if not inSources:
                        buf.append(line)
                    continue
                name = spl[0].strip()
                if name == "source":
                    hitSources = True
                    inSources = True
                    continue
                elif name == "version":
                    buf.append("%s: %s" % (spl[0], newversion))
                elif name == "release":
                    val = int(spl[1].strip()) + 1
                    buf.append("%s: %s" % (spl[0], val))
                elif name.startswith("-") and inSources:
                    continue
                else:
                    inSources = False
                    buf.append(line)
            else:
                buf.append(line)

    buf = list()
    buf.extend(bufTop)
    buf.append("source     :")
    buf.append("    - %s : %s" % (url, sha256))
    buf.extend(bufEnd)

    os.unlink(file)

    try:
        f = open(ymlfile, "w")
        f.writelines(["%s\n" % x for x in buf])
        f.close()
    except Exception, e:
        print "Error writing file, may need to reset it."
        print e
        sys.exit(1)

