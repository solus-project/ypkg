#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  This file is part of ypkg2
#
#  Copyright 2015-2016 Ikey Doherty <ikey@solus-project.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#

from . import console_ui
from .stringglob import StringPathGlob

import os

PRIORITY_DEFAULT = 0    # Standard internal priority for a pattern
PRIORITY_USER = 100     # Priority for a user pattern, do what they say.


class PackageGenerator:

    patterns = None
    packages = None

    def __init__(self):
        self.patterns = dict()
        self.packages = dict()

        # Dummy code for testing
        self.add_pattern("/usr/lib64/*.so", "devel")
        self.add_pattern("/usr/lib/*.so", "devel")
        self.add_pattern("/usr/lib64/pkgconfig/*.pc", "devel")
        self.add_pattern("/usr/lib/pkgconfig/*.pc", "devel")
        # self.add_pattern("/usr/share/gtk-doc/html/", "docs")

        self.add_pattern("/usr/lib/lib*.so.*", "main")
        self.add_pattern("/usr/lib64/lib*.so.*", "main")

        # Test override
        self.add_pattern("/usr/lib/pkgconfig/*wayland*.pc", "wayland-devel",
                         priority=PRIORITY_USER)
        self.add_pattern("/usr/lib/libgailutil-3.so.0.0.0", "roflcopter",
                         priority=PRIORITY_USER)

    def add_file(self, path):
        """ Add a file path to the owned list and place it into the correct
            package (main or named subpackage) according to the highest found
            priority pattern rule, otherwise it shall fallback under default
            policy into the main package itself.

            This enables a fallback approach, whereby subpackages "steal" from
            the main listing, and everything that is left is packaged into the
            main package (YpkgSpec::name), making "abandoned" files utterly
            impossible. """

        target = "main"  # default pattern name
        pattern = self.get_pattern(path)
        if pattern:
            target = self.patterns[pattern]

        # TODO: Change out for our old pkg object
        if target not in self.packages:
            self.packages[target] = set()
        self.packages[target].add(path)

    def remove_file(self, path):
        """ Remove a file from our set, in any of our main or sub packages
            that may currently own it. """
        pass

    def get_pattern(self, path):
        """ Return a matching pattern for the given path.
            This is ordered according to priority to enable
            multiple layers of priorities """
        matches = [p for p in self.patterns if p.match(path)]
        if len(matches) == 0:
            return None

        matches = sorted(matches, key=StringPathGlob.get_priority,
                         reverse=True)
        return matches[0]

    def add_pattern(self, pattern, pkgName, priority=PRIORITY_DEFAULT):
        """ Add a pattern to the internal map according to the
            given priority. """

        obj = None
        is_prefix = False
        if pattern.endswith(os.sep):
            if not StringPathGlob.is_a_pattern(pattern):
                is_prefix = True

        obj = StringPathGlob(pattern, prefixMatch=is_prefix, priority=priority)
        self.patterns[obj] = pkgName

    def emit_packages(self):
        """ Ensure we've finalized our state, allowing proper theft and
            exclusion to take place, and then return all package objects
            that we've managed to generate. There is no gaurantee that
            a "main" package will be generated, as patterns may omit
            the production of one. """
        return []
