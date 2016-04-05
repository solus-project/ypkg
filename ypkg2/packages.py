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


PRIORITY_DEFAULT = 0    # Standard internal priority for a pattern
PRIORITY_USER = 100     # Priority for a user pattern, do what they say.


class PackageGenerator:

    packages = None

    def __init__(self):
        packages = dict()

    def add_file(self, path):
        """ Add a file path to the owned list and place it into the correct
            package (main or named subpackage) according to the highest found
            priority pattern rule, otherwise it shall fallback under default
            policy into the main package itself.

            This enables a fallback approach, whereby subpackages "steal" from
            the main listing, and everything that is left is packaged into the
            main package (YpkgSpec::name), making "abandoned" files utterly
            impossible. """
        pass

    def remove_file(self, path):
        """ Remove a file from our set, in any of our main or sub packages
            that may currently own it. """
        pass

    def get_pattern(self, path):
        """ Return a matching pattern for the given path.
            This is ordered according to priority to enable
            multiple layers of priorities """
        return None

    def add_pattern(self, pkgName, pattern, priority=PRIORITY_DEFAULT):
        """ Add a pattern to the internal map according to the
            given priority. """
        pass

    def emit_packages(self):
        """ Ensure we've finalized our state, allowing proper theft and
            exclusion to take place, and then return all package objects
            that we've managed to generate. There is no gaurantee that
            a "main" package will be generated, as patterns may omit
            the production of one. """
        return []
