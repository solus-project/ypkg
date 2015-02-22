#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  ypkg.py
#  
#  Copyright 2015 Ikey Doherty <ikey@evolve-os.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
import sys

sys.path.append("/usr/share/ypkg")

import build
import packageit
import subprocess
import shlex
import sanity
from sanity import sane
import os
import shutil

def main():
    if len(sys.argv) < 2:
        print "Not enough arguments"
        return 1

    fpath = sys.argv[1]
    if not os.path.exists(fpath):
        print "%s does not exist.." % fpath
        return 1
    if not fpath.endswith("package.yml"):
        print "Unnecessarily anal warning: File is not named package.yml"
        return 1

    if not sane(fpath): # then y made for linoox
        return 1

    pspec = build.BuildPrefix + "/%s.xml" % sanity.name
    actions = build.BuildPrefix + "/actions.py"

    build.BuildDir += "/%s" % sanity.name
    build.InstallDir += "/%s" % sanity.name

    build.cleanup()
    sources = sanity.get_sources()
    tars = build.fetch_source(sources)
    build.extract(tars)

    try:
        build.build(fpath)
    except Exception, e:
        print "Build failure: %s" % e
        return 1

    packageit.packageit(fpath, build.InstallDir, pspec)
    f = open(actions, "w")
    tmpl = """
from pisi.actionsapi import pisitools

def install():
    pisitools.insinto("/", "%s/*")
""" % build.InstallDir


    f.writelines(tmpl)
    f.close()

    ret = subprocess.call(shlex.split("sudo eopkg build %s" % pspec), shell=False)
    if ret != 0:
        print "Failed to build package"
        return ret

    try:
        shutil.copy(pspec, "%s/pspec.xml" % os.getcwd())
    except:
        print "Unable to copy pspec.xml to current directory!"
        return 1
    
    return 0    

if __name__ == "__main__":
    sys.exit(main())
