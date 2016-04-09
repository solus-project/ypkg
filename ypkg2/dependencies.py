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
from pisi.db.filesdb import FilesDB
import os


class DependencyResolver:

    idb = None
    pdb = None
    fdb = None

    global_rpaths = set()
    global_sonames = dict()
    global_pkgconfigs = dict()
    global_pkgconfig32s = dict()
    gene = None

    bindeps_cache = dict()
    bindeps_emul32 = dict()

    pkgconfig_cache = dict()
    pkgconfig32_cache = dict()

    def search_file(self, fname):
        if fname[0] == '/':
            fname = fname[1:]
        return self.fdb.search_file(fname)

    def __init__(self):
        """ Allows us to do look ups on all packages """
        self.idb = InstallDB()
        self.pdb = PackageDB()
        self.fdb = FilesDB()

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

    def get_symbol_external(self, info, symbol, paths=None):
        """ Get the provider of the required symbol from the files database,
            i.e. installed binary dependencies
        """
        # Try a cached approach first.
        if info.emul32:
            if symbol in self.bindeps_emul32:
                return self.bindeps_emul32[symbol]
        else:
            if symbol in self.bindeps_cache:
                return self.bindeps_cache[symbol]

        if not paths:
            paths = ["/usr/lib64", "/usr/lib"]
            if info.emul32:
                paths = ["/usr/lib32", "/usr/lib", "/usr/lib64"]

            if info.rpaths:
                paths.extend(info.rpaths)

        pkg = None
        for path in paths:
            fpath = os.path.join(path, symbol)
            pkg = self.search_file(fpath)
            if pkg:
                lpkg = pkg[0][0]
                if info.emul32:
                    self.bindeps_emul32[symbol] = lpkg
                else:
                    self.bindeps_cache[symbol] = lpkg
                console_ui.emit_info("Dependency",
                                     "{} adds dependency on {} from {}".
                                     format(info.pretty, symbol, lpkg))
                return lpkg
        return None

    def get_pkgconfig_provider(self, info, name):
        """ Get the internal provider for a pkgconfig name """
        if info.emul32:
            if name in self.global_pkgconfig32s:
                pkg = self.global_pkgconfig32s[name]
                return self.ctx.spec.get_package_name(pkg)
        if name in self.global_pkgconfigs:
            pkg = self.global_pkgconfigs[name]
            return self.ctx.spec.get_package_name(pkg)

    def get_pkgconfig_external(self, info, name):
        """ Get the external provider of a pkgconfig name """
        pkg = None

        if info.emul32:
            if name in self.pkgconfig32_cache:
                return self.pkgconfig32_cache[name]
        if name in self.pkgconfig_cache:
            return self.pkgconfig_cache[name]

        if info.emul32:
            pkg = self.idb.get_package_by_pkgconfig32(name)
            if not pkg:
                pkg = self.idb.get_package_by_pkgconfig(name)
            if not pkg:
                pkg = self.pdb.get_package_by_pkgconfig32(name)
            if not pkg:
                pkg = self.pdb.get_package_by_pkgconfig(name)
        else:
            pkg = self.idb.get_package_by_pkgconfig(name)
            if not pkg:
                pkg = self.pdb.get_package_by_pkgconfig(name)

        if not pkg:
            return None
        if info.emul32:
            self.pkgconfig32_cache[name] = pkg.name
        else:
            self.pkgconfig_cache[name] = pkg.name

        return pkg.name

    def handle_binary_deps(self, packageName, info):
        """ Handle direct binary dependencies """
        for sym in info.symbol_deps:
            r = self.get_symbol_provider(sym)
            if not r:
                r = self.get_symbol_external(info, sym)
                if not r:
                    print("Fatal: Unknown symbol: {}".format(sym))
                    continue
            self.gene.packages[packageName].depend_packages.add(r)

    def handle_pkgconfig_deps(self, packageName, info):
        """ Handle pkgconfig dependencies """
        for item in info.pkgconfig_deps:
            pkgName = self.ctx.spec.get_package_name(packageName)

            prov = self.get_pkgconfig_provider(info, item)
            if prov:
                print("internal: {}/{} depends on {}.pc from {}".
                      format(pkgName, info.pretty, item, prov))
                continue
            prov = self.get_pkgconfig_external(info, item)
            if not prov:
                print("Fatal: Unknown pc: {}".format(item))
            print("External pc dep: {}, {}".
                  format(pkgName, prov))
            print(prov)

    def handle_pkgconfig_provides(self, packageName, info):
        adder = None
        if info.emul32:
            adder = "pkgconfig32({})".format(info.pkgconfig_name)
        else:
            adder = "pkgconfig({})".format(info.pkgconfig_name)
        # TODO: Add versioning in examine.py .. ?
        self.gene.packages[packageName].provided_symbols.add(adder)
        pass

    def handle_soname_links(self, packageName, info):
        """ Add dependencies between packages due to a .so splitting """
        ourName = self.ctx.spec.get_package_name(packageName)

        for link in info.soname_links:
            fi = self.gene.get_file_owner(link)
            if not fi:
                console_ui.emit_warning("SOLINK", "{} depends on non existing"
                                        "soname link: {}".
                                        format(packageName, link))
                continue
            pkgName = self.ctx.spec.get_package_name(fi.name)
            if pkgName == ourName:
                continue
            self.gene.packages[packageName].depend_packages.add(pkgName)
            console_ui.emit_info("SOLINK", "{} depends on {} through .so link".
                                 format(ourName, pkgName))

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
                if info.symbol_deps:
                    self.handle_binary_deps(packageName, info)

                if info.pkgconfig_deps:
                    self.handle_pkgconfig_deps(packageName, info)

                if info.pkgconfig_name:
                    self.handle_pkgconfig_provides(packageName, info)

                if info.soname_links:
                    self.handle_soname_links(packageName, info)
        return True
