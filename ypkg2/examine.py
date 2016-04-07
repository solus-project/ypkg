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
import magic
import re
import os
import subprocess


class PackageExaminer:
    """ Responsible for identifying files suitable for further examination,
        such as those that should be removed, checked for dependencies,
        providers, and even those that should be stripped
    """

    def __init__(self):
        self.v_dyn = re.compile(r"ELF (64|32)\-bit LSB shared object,")
        self.v_bin = re.compile(r"ELF (64|32)\-bit LSB executable,")
        self.v_rel = re.compile(r"ELF (64|32)\-bit LSB relocatable,")
        self.shared_lib = re.compile(r".*Shared library: \[(.*)\].*")
        self.r_path = re.compile(r".*Library rpath: \[(.*)\].*")
        self.r_soname = re.compile(r".*Library soname: \[(.*)\].*")

    def strip_file(self, context, pretty, file, mode=None):
        """ Schedule a strip, basically. """
        if not context.spec.pkg_strip:
            return
        exports = ["LC_ALL=C"]
        if context.spec.pkg_optimize == "speed":
            exports.extend([
                "AR=\"gcc-ar\"",
                "RANLIB=\"gcc-ranlib\"",
                "NM=\"gcc-nm\""])

        cmd = "{} strip {} \"{}\""
        flags = ""
        if mode == "shared":
            flags = "--strip-unneeded"
        elif mode == "ko":
            flags = "-g --strip-unneeded"
        elif mode == "ar":
            flags = "--strip-debug"
        try:
            s = " ".join(exports)
            subprocess.check_call(cmd.format(s, flags, file), shell=True)
            console_ui.emit_info("Stripped", pretty)
        except Exception as e:
            console_ui.emit_warning("Strip", "Failed to strip '{}'".
                                    format(pretty))
            print(e)

    def examine_file(self, context, package, pretty, file, magic_string):

        if self.v_dyn.match(magic_string):
            # Get soname, direct deps and strip
            self.strip_file(context, pretty, file, mode="shared")
        elif self.v_bin.match(magic_string):
            # Get direct deps, and strip
            self.strip_file(context, pretty, file, mode="executable")
        elif self.v_rel.match(magic_string):
            # Kernel object in all probability
            if file.endswith(".ko"):
                self.strip_file(context, pretty, file, mode="ko")
        elif magic_string == "current ar archive":
            # Strip only.
            self.strip_file(context, pretty, file, mode="ar")
        else:
            return True
        return True

    def examine_package(self, context, package):
        """ Examine the given package and update symbols, etc. """
        install_dir = context.get_install_dir()

        # Right now we actually only care about magic matching
        for file in package.emit_files():
            if file[0] == '/':
                file = file[1:]
            fpath = os.path.join(install_dir, file)
            try:
                mgs = magic.from_file(fpath)
            except Exception as e:
                print(e)
                continue
            if not self.examine_file(context, package, "/" + file, fpath, mgs):
                return False
        return True

    def examine_packages(self, context, packages):
        """ Examine all packages, in order to update dependencies, etc """
        console_ui.emit_info("Examine", "Examining packages")
        for package in packages:
            if not self.examine_package(context, package):
                return False

        return True
