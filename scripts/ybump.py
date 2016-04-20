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
import sys
import ruamel.yaml


def usage(msg=None, ex=1):
    if msg:
        print(msg)
    else:
        print("Usage: %s file.yml" % sys.argv[0])
    sys.exit(ex)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        usage()

    with open(sys.argv[1]) as fp:
        data = ruamel.yaml.round_trip_load(fp)
    data['release'] += 1
    try:
        with open(sys.argv[1], 'w') as fp:
            ruamel.yaml.round_trip_dump(
                data, fp, indent=4, block_seq_indent=4,
                top_level_colon_align=True, prefix_colon=' ')
    except Exception as e:
        print("Error writing file, may need to reset it.")
        print(e)
        sys.exit(1)
