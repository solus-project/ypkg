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
from .metadata import readlink
from . import remove_prefix
from . import EMUL32PC
import magic
import re
import os
import subprocess
import shutil
import multiprocessing

global share_ctx


v_dyn = re.compile(r"ELF (64|32)\-bit LSB shared object,")
v_bin = re.compile(r"ELF (64|32)\-bit LSB executable,")
v_rel = re.compile(r"ELF (64|32)\-bit LSB relocatable,")
shared_lib = re.compile(r".*Shared library: \[(.*)\].*")
r_path = re.compile(r".*Library rpath: \[(.*)\].*")
r_soname = re.compile(r".*Library soname: \[(.*)\].*")


def is_pkgconfig_file(pretty, mgs):
    """ Simple as it sounds, work out if this is a pkgconfig file """
    if pretty.endswith(".pc"):
        pname = os.path.basename(os.path.dirname(pretty))
        if pname == "pkgconfig" and "ASCII" in mgs:
            return True
    return False


def is_soname_link(file, mgs):
    """ Used to detect soname links """
    if not file.endswith(".so"):
        return False

    if os.path.islink(file) and not os.path.isdir(file):
        return True
    return False


class FileReport:

    pkgconfig_deps = None
    pkgconfig_name = None

    emul32 = False

    soname = None
    symbol_deps = None

    rpaths = None

    soname_links = None

    def scan_binary(self, file, check_soname=False):
        cmd = "LC_ALL=C /usr/bin/readelf -d \"{}\"".format(file)
        try:
            output = subprocess.check_output(cmd, shell=True)
        except Exception as e:
            console_ui.emit_warning("File", "Failed to scan binary deps for"
                                    " path: {}".format(file))
        for line in output.split("\n"):
            line = line.strip()

            # Match rpath
            r = r_path.match(line)
            if r:
                if self.rpaths is None:
                    self.rpaths = set()
                self.rpaths.add(r.group(1))
                continue

            # Match direct needed dependency
            m = shared_lib.match(line)
            if m:
                if self.symbol_deps is None:
                    self.symbol_deps = set()
                self.symbol_deps.add(m.group(1))
                continue

            # Check the soname for this binary file
            if check_soname:
                so = r_soname.match(line)
                if so:
                    self.soname = so.group(1)

    def scan_pkgconfig(self, file):
        sub = ""
        if self.emul32:
            sub = "PKG_CONFIG_PATH=\"{}\" ".format(EMUL32PC)

        cmds = [
            "LC_ALL=C {}pkg-config --print-requires \"{}\"",
            "LC_ALL=C {}pkg-config --print-requires-private \"{}\""
        ]

        pcname = os.path.basename(file).split(".pc")[0]
        self.pkgconfig_name = pcname

        if not share_ctx.spec.pkg_autodep:
            return
        for cmd in cmds:
            try:
                out = subprocess.check_output(cmd.format(sub, file),
                                              shell=True)
            except Exception as e:
                print(e)
                continue
            for line in out.split("\n"):
                line = line.strip()

                if line == "":
                    continue
                name = None
                # In future we'll do something useful with versions
                if ">=" in line:
                    name = line.split(">=")[0]
                elif "=" in line:
                    # This is an internal dependency
                    name = line.split("=")[0]
                else:
                    name = line
                name = name.strip()

                if not self.pkgconfig_deps:
                    self.pkgconfig_deps = set()
                self.pkgconfig_deps.add(name)

    def add_solink(self, file, pretty):
        """ .so links are almost always split into -devel subpackages in ypkg,
            unless explicitly overriden. However, they are useless without the
            actual versioned so they link to. Therefore, we add an automatic
            dependency to the hosting package when we find one of these, i.e:

            zlib:
                /usr/lib64/libz.so.1.2.8
            zlib-devel:
                /usr/lib64/libz.so -> libz.so.1.2.8

            zlib-devel -> zlib
            """
        fpath = readlink(file)

        dirn = os.path.dirname(file)
        fobj = os.path.join(dirn, fpath)

        try:
            mg = magic.from_file(fobj)
        except Exception as e:
            return

        if not v_dyn.match(mg):
            return
        fpath = remove_prefix(fobj, share_ctx.get_install_dir())
        if not self.soname_links:
            self.soname_links = set()
        self.soname_links.add(fpath)

    def __init__(self, pretty, file, mgs):
        global share_ctx
        self.pretty = pretty
        self.file = file

        if pretty.startswith("/usr/lib32/") or pretty.startswith("/lib32"):
            self.emul32 = True
        if is_pkgconfig_file(pretty, mgs):
            self.scan_pkgconfig(file)

        # Some things omit automatic dependencies
        if share_ctx.spec.pkg_autodep:
            if is_soname_link(file, mgs):
                self.add_solink(file, pretty)
            elif v_dyn.match(mgs):
                self.scan_binary(file, True)
            elif v_bin.match(mgs):
                self.scan_binary(file, False)


def strip_file(context, pretty, file, magic_string, mode=None):
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


def get_debug_path(context, file, magic_string):
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


def examine_file(*args):
    global share_ctx
    package = args[0]
    pretty = args[1]
    file = args[2]
    mgs = args[3]

    context = share_ctx

    if v_dyn.match(mgs):
        # Get soname, direct deps and strip
        store_debug(context, pretty, file, mgs)
        strip_file(context, pretty, file, mgs, mode="shared")
    elif v_bin.match(mgs):
        # Get direct deps, and strip
        store_debug(context, pretty, file, mgs)
        strip_file(context, pretty, file, mgs, mode="executable")
    elif v_rel.match(mgs):
        # Kernel object in all probability
        if file.endswith(".ko"):
            store_debug(context, pretty, file, mgs)
            strip_file(context, pretty, file, mgs, mode="ko")
    elif mgs == "current ar archive":
        # Strip only.
        strip_file(context, pretty, file, mgs, mode="ar")

    freport = FileReport(pretty, file, mgs)
    return freport


def store_debug(context, pretty, file, magic_string):
    if not context.can_dbginfo:
        return

    did = get_debug_path(context, file, magic_string)

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


class PackageExaminer:
    """ Responsible for identifying files suitable for further examination,
        such as those that should be removed, checked for dependencies,
        providers, and even those that should be stripped
    """

    def __init__(self):
        self.libtool_file = re.compile("libtool library file, ASCII text.*")

    def should_nuke_file(self, pretty, file, mgs):
        # it's not that we hate.. Actually, no, we do. We hate you libtool.
        if self.libtool_file.match(mgs):
            return True
        if pretty == "/usr/share/info/dir":
            return True
        if pretty.startswith("/emul32"):
            return True
        return False

    def file_is_of_interest(self, pretty, file, mgs):
        """ So we can keep our list of things to check low """
        if v_dyn.match(mgs) or v_bin.match(mgs) or v_rel.match(mgs):
            return True
        if is_pkgconfig_file(pretty, mgs):
            return True
        if is_soname_link(file, mgs):
            return True
        return False

    def examine_package(self, context, package):
        """ Examine the given package and update symbols, etc. """
        install_dir = context.get_install_dir()

        global share_ctx

        share_ctx = context

        # Right now we actually only care about magic matching
        removed = set()

        # pool = multiprocessing.Pool()
        results = list()

        for file in package.emit_files():
            if file[0] == '/':
                file = file[1:]
            fpath = os.path.join(install_dir, file)
            try:
                mgs = magic.from_file(fpath)
            except Exception as e:
                print(e)
                continue
            if self.should_nuke_file("/" + file, fpath, mgs):
                try:
                    if os.path.isfile(fpath):
                        os.unlink(fpath)
                    else:
                        shutil.rmtree(fpath)
                except Exception as e:
                    console_ui.emit_error("Clean", "Failed to remove unwanted"
                                          "file: {}".format(e))
                    return False
                console_ui.emit_info("Clean", "Removed unwanted file: {}".
                                     format("/" + file))
                removed.add("/" + file)

            if not self.file_is_of_interest("/" + file, fpath, mgs):
                continue
            # Handle this asynchronously
            results.append(examine_file(package, "/" + file, fpath, mgs))
            # results.append(pool.apply_async(examine_file, [
            #               package, "/" + file, fpath, mgs],
            #               callback=None))

        # pool.close()
        # pool.join()

        # infos = [x.get() for x in results]

        for r in removed:
            package.remove_file(r)
        return results

    def examine_packages(self, context, packages):
        """ Examine all packages, in order to update dependencies, etc """
        console_ui.emit_info("Examine", "Examining packages")

        examinations = dict()
        for package in packages:
            ir = self.examine_package(context, package)
            if not ir:
                continue
            examinations[package.name] = ir
        return examinations
