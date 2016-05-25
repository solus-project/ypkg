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
import ruamel.yaml
import os
import subprocess
import pisi.version


def usage(msg=None, ex=1):
    if msg:
        print(msg)
    else:
        print("Usage: %s" % sys.argv[0])
    sys.exit(ex)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        usage()

    ymlfile = "package.yml"
    if not os.path.exists(ymlfile):
        usage("Specified file does not exist")
    if not ymlfile.endswith(".yml"):
        usage("%s does not look like a valid package.yml file")

    newversion = sys.argv[1]
    try:
        d = pisi.version.Version(newversion)
    except Exception as e:
        print("Problematic version string: %s" % e)
        sys.exit(1)

    url = sys.argv[2]
    file = url.split("/")[-1]

    try:
        r = os.system("wget \"%s\"" % url)
    except:
        print("Failed to download file")
        sys.exit(1)
    if r != 0:
        print("Failed to download file")
        sys.exit(1)

    sha256 = subprocess.check_output(["sha256sum",  file]).split()[0].strip()

    with open(ymlfile, "r") as infile:
        data = ruamel.yaml.round_trip_load(infile)
    data['source'] = sources = []
    sources.append({url: sha256})
    data['release'] += 1
    data['version'] = newversion

    os.unlink(file)

    try:
        with open(ymlfile, 'w') as fp:
            ruamel.yaml.round_trip_dump(
                data, fp, indent=4, block_seq_indent=4, width=200,
                top_level_colon_align=True, prefix_colon=' ')
    except Exception as e:
        print("Error writing file, may need to reset it.")
        print(e)
        sys.exit(1)
