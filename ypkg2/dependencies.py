#!/bin/true
# -*- coding: utf-8 -*-
#
#  This file is part of ypkg2
#
#  Copyright 2015-2016 Ikey Doherty <ikey@solus-project.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#

from . import console_ui
from pisi.db.installdb import InstallDB
from pisi.db.packagedb import PackageDB


class DependencyResolver:

    idb = None
    pdb = None

    global_rpaths = set()
    global_sonames = set()
    global_pkgconfigs = set()
    global_pkgconfig32s = set()

    def __init__(self):
        """ Allows us to do look ups on all packages """
        self.idb = InstallDB()
        self.pdb = PackageDB()

    def compute_for_packages(self, context, packageSet):
        """ packageSet is a dict mapping here. """

        # First iteration, collect the globals
        for packageName in packageSet:
            for info in packageSet[packageName]:
                if info.rpaths:
                    self.global_rpaths.update(info.rpaths)
                if info.soname:
                    self.global_sonames.add(info.soname)
                if info.pkgconfig_name:
                    if info.emul32:
                        self.global_pkgconfig32s.add(info.pkgconfig_name)
                    else:
                        self.global_pkgconfigs.add(info.pkgconfig_name)

        print("Global rpaths: {}".format(", ".join(self.global_rpaths)))
        print("Global sonames: {}".format(", ".join(self.global_sonames)))

        return False
