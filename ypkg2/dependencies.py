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
import os


class DependencyResolver:

    idb = None
    pdb = None

    global_rpaths = set()
    global_sonames = dict()
    global_pkgconfigs = dict()
    global_pkgconfig32s = dict()
    gene = None

    def __init__(self):
        """ Allows us to do look ups on all packages """
        self.idb = InstallDB()
        self.pdb = PackageDB()

    def get_symbol_provider(self, symbol):
        """ Grab the symbol from the local packages """
        if symbol in self.global_sonames:
            pkgname = self.global_sonames[symbol]
            return self.ctx.spec.get_package_name(pkgname)
        # Check if its in any rpath
        for rpath in self.global_rpaths:
            fpath = os.path.join(rpath, symbol)
            pkg = self.gene.get_file_owner(fpath)
            if pkg:
                return self.ctx.spec.get_package_name(pkg.name)
        return None

    def compute_for_packages(self, context, gene, packageSet):
        """ packageSet is a dict mapping here. """
        self.gene = gene
        self.packageSet = packageSet
        self.ctx = context

        # First iteration, collect the globals
        for packageName in packageSet:
            for info in packageSet[packageName]:
                if info.rpaths:
                    self.global_rpaths.update(info.rpaths)
                if info.soname:
                    self.global_sonames[info.soname] = packageName
                if info.pkgconfig_name:
                    pcName = info.pkgconfig_name
                    if info.emul32:
                        self.global_pkgconfig32s[pcName] = packageName
                    else:
                        self.global_pkgconfigs[pcName] = packageName

        # Ok now find the dependencies
        for packageName in packageSet:
            for info in packageSet[packageName]:
                if not info.symbol_deps:
                    continue
                for sym in info.symbol_deps:
                    r = self.get_symbol_provider(sym)
                    if not r:
                        continue
                    print("{} depends on {} from {}".
                          format(info.pretty, sym, r))

        print("Global rpaths: {}".format(", ".join(self.global_rpaths)))
        print("Global sonames: {}".
              format(", ".join(self.global_sonames.values())))

        return False
