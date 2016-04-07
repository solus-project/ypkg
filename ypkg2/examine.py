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
        self.libtool_file = re.compile("libtool library file, ASCII text.*")

    def get_debug_path(self, context, file, magic_string):
        """ Grab the NT_GNU_BUILD_ID """
        cmd = "LC_ALL=C readelf -n \"{}\"".format(file)
        try:
            lines = subprocess.check_output(cmd, shell=True)
        except Exception as e:
            return None

        for line in lines.split("\n"):
            if "Build ID:" not in line:
                continue
            v = line.split(":")[1].strip()

            libdir = "/usr/lib"
            if "ELF 32" in magic_string:
                libdir = "/usr/lib32"

            path = os.path.join(libdir, "debug", ".build-id", v[0:2], v[2:])
            return path + ".debug"
        return None

    def store_debug(self, context, pretty, file, magic_string):
        did = self.get_debug_path(context, file, magic_string)

        if did is None:
            if "ELF 32" in magic_string:
                did = "/usr/lib32/debug/{}.debug".format(pretty)
            else:
                did = "/usr/lib/debug/{}.debug".format(pretty)

        did_full = os.path.join(context.get_install_dir(), did[1:])

        dirs = os.path.dirname(did_full)
        if not os.path.exists(dirs):
            try:
                os.makedirs(dirs, mode=00755)
            except Exception as e:
                console_ui.emit_error("Debug", "Failed to make directory")
                print e
                return

        cmd = "objcopy --only-keep-debug \"{}\" \"{}\"".format(file, did_full)
        try:
            subprocess.check_call(cmd, shell=True)
        except Exception as e:
            console_ui.emit_warning("objcopy", "Failed --only-keep-debug")
            return
        cmd = "objcopy --add-gnu-debuglink=\"{}\" \"{}\"".format(did_full,
                                                                 file)
        try:
            subprocess.check_call(cmd, shell=True)
        except Exception as e:
            console_ui.emit_warning("objcopy", "Failed --add-gnu-debuglink")
            return

    def strip_file(self, context, pretty, file, magic_string, mode=None):
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

    def examine_file(self, context, package, pretty, file, mgs):

        if self.v_dyn.match(mgs):
            # Get soname, direct deps and strip
            self.store_debug(context, pretty, file, mgs)
            self.strip_file(context, pretty, file, mgs, mode="shared")
        elif self.v_bin.match(mgs):
            # Get direct deps, and strip
            self.store_debug(context, pretty, file, mgs)
            self.strip_file(context, pretty, file, mgs, mode="executable")
        elif self.v_rel.match(mgs):
            # Kernel object in all probability
            if file.endswith(".ko"):
                self.store_debug(context, pretty, file, mgs)
                self.strip_file(context, pretty, file, mgs, mode="ko")
        elif mgs == "current ar archive":
            # Strip only.
            self.strip_file(context, pretty, file, mgs, mode="ar")
        else:
            return True
        return True

    def should_nuke_file(self, pretty, file, mgs):
        # it's not that we hate.. Actually, no, we do. We hate you libtool.
        if self.libtool_file.match(mgs):
            return True
        if pretty == "/usr/share/info/dir":
            return True
        return False

    def examine_package(self, context, package):
        """ Examine the given package and update symbols, etc. """
        install_dir = context.get_install_dir()

        # Right now we actually only care about magic matching
        removed = set()

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
            if self.should_nuke_file("/" + file, fpath, mgs):
                try:
                    os.unlink(fpath)
                except Exception as e:
                    console_ui.emit_error("Clean", "Failed to remove unwanted"
                                          "file: {}".format(e))
                    return False
                console_ui.emit_info("Clean", "Removed unwanted file: {}".
                                     format("/" + file))
                removed.add("/" + file)

        for r in removed:
            package.remove_file(r)

        return True

    def examine_packages(self, context, packages):
        """ Examine all packages, in order to update dependencies, etc """
        console_ui.emit_info("Examine", "Examining packages")
        for package in packages:
            if not self.examine_package(context, package):
                return False

        return True
