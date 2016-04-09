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

import pisi.config
import os
import shutil

# These flag sets are courtesy of autospec in
# Clear Linux Project For Intel Architecture
SPEED_FLAGS = "-flto -ffunction-sections -fno-semantic-interposition -O3"
SIZE_FLAGS = "-Os -ffunction-sections"
PGO_GEN_FLAGS = "-fprofile-generate -fprofile-dir=\"{}\""
PGO_USE_FLAGS = "-fprofile-use -fprofile-dir=\"{}\" -fprofile-correction"


class Flags:

    C = 0
    CXX = 1
    LD = 2

    @staticmethod
    def get_desc(f):
        ''' Get descriptor for flag type '''
        if f == Flags.C:
            return "CFLAGS"
        elif f == Flags.CXX:
            return "CXXFLAGS"
        elif f == Flags.LD:
            return "LDFLAGS"
        else:
            return "UNKNOWN_FLAG_SET_CHECK_IT"

    @staticmethod
    def filter_flags(f, filters):
        """ Filter the flags from this set """
        nflags = filter(lambda s: s not in filters, f)
        return nflags

    @staticmethod
    def optimize_flags(f, opt_type):
        """ Optimize this flag set for a given optimisation type """
        optimisations = ["-O%s" % x for x in range(0, 4)]
        optimisations.extend("-Os")

        newflags = Flags.filter_flags(f, optimisations)

        if opt_type == "speed":
            newflags.extend(SPEED_FLAGS.split(" "))
        elif opt_type == "size":
            newflags.extend(SIZE_FLAGS.split(" "))
        else:
            console_ui.emit_warning("Flags", "Uknown optimization: {}".
                                    format(opt_type))
            return f
        return newflags

    @staticmethod
    def pgo_gen_flags(f, d):
        """ Update flags with PGO generator flags """
        r = list(f)
        r.extend((PGO_GEN_FLAGS.format(d).split(" ")))
        return r

    @staticmethod
    def pgo_use_flags(f, d):
        """ Update flags with PGO use flags """
        r = list(f)
        r.extend((PGO_USE_FLAGS.format(d).split(" ")))
        return r


class BuildConfig:

    arch = None
    host = None
    ccache = None

    cflags = None
    cxxflags = None
    ldflags = None

    cc = None
    cxx = None

    ld_as_needed = True  # Make this configurable at some point.

    jobcount = 2

    def get_flags(self, t):
        """ Simple switch to grab a set of flags by a type """
        if t == Flags.C:
            return self.cflags
        if t == Flags.CXX:
            return self.cxxflags
        if t == Flags.LD:
            return self.ldflags
        return set([])


class YpkgContext:
    """ Base context for things like cflags, etc """

    build = None

    global_archive_dir = None
    is_root = False
    spec = None
    emul32 = False
    files_dir = None
    pconfig = None

    can_dbginfo = False

    def __init__(self, spec, emul32=False):
        self.spec = spec
        self.emul32 = emul32
        self.build = BuildConfig()
        self.init_config()
        if os.geteuid() == 0 and "FAKED_MODE" not in os.environ:
            self.is_root = True

    def get_path(self):
        """ Return the path, mutated to include ccache if needed """
        default_path = "/usr/bin:/bin:/usr/sbin:/sbin"

        if not self.spec.pkg_ccache:
            return default_path
        if not self.build.ccache:
            return default_path

        ccaches = ["/usr/lib64/ccache/bin", "/usr/lib/ccache/bin"]
        for i in ccaches:
            if os.path.exists(i):
                console_ui.emit_info("Build", "Enabling ccache")
                return "{}:{}".format(i, default_path)
        return default_path

    def get_sources_directory(self):
        """ Get the configured source directory for fetching sources to """
        if self.is_root:
            return self.global_archive_dir
        return os.path.join(self.get_build_prefix(), "sources")

    def get_build_prefix(self):
        """ Get the build prefix used by ypkg """
        if self.is_root:
            return "/var/ypkg-root"
        return "{}/YPKG".format(os.path.expanduser("~"))

    def get_install_dir(self):
        """ Get the install directory for the given package """
        return os.path.abspath("{}/root/{}/install".format(
                               self.get_build_prefix(),
                               self.spec.pkg_name))

    def get_packaging_dir(self):
        """ The temporary packaging directory """
        return os.path.abspath("{}/root/{}/pkg".format(
                               self.get_build_prefix(),
                               self.spec.pkg_name))

    def get_build_dir(self):
        """ Get the build directory for the given package """
        buildSuffix = "build"
        if self.emul32:
            buildSuffix = "build-32"

        return os.path.abspath("{}/root/{}/{}".format(
                               self.get_build_prefix(),
                               self.spec.pkg_name,
                               buildSuffix))

    def get_pgo_dir(self):
        """ Get the PGO data directory for the given package """
        pgoSuffix = "pgo"
        if self.emul32:
            pgoSuffix = "pgo-32"

        return os.path.abspath("{}/root/{}/{}".format(
                                self.get_build_prefix(),
                                self.spec.pkg_name,
                                pgoSuffix))

    def init_config(self):
        """ Initialise our configuration prior to building """
        conf = pisi.config.Config()

        # For now follow the eopkg.conf..
        self.build.host = conf.values.build.host
        self.build.arch = conf.values.build.arch
        self.build.cflags = list(conf.values.build.cflags.split(" "))
        self.build.cxxflags = list(conf.values.build.cxxflags.split(" "))
        self.build.ldflags = list(conf.values.build.ldflags.split(" "))
        self.build.ccache = "ccache" in conf.values.build.buildhelper

        self.can_dbginfo = conf.values.build.generatedebug
        self.pconfig = conf

        if self.spec.pkg_clang:
            self.build.cc = "clang"
            self.build.cxx = "clang++"
        else:
            self.build.cc = "{}-gcc".format(conf.values.build.host)
            self.build.cxx = "{}-g++".format(conf.values.build.host)

        if self.spec.pkg_optimize is not None:
            self.build.cflags = Flags.optimize_flags(self.build.cflags,
                                                     self.spec.pkg_optimize)

        if self.emul32:
            ncflags = list()
            for flag in self.build.cflags:
                if flag.startswith("-march="):
                    flag = "-march=i686"
                ncflags.append(flag)
            self.build.cflags = ncflags
            ncxxflags = list()
            for flag in self.build.cxxflags:
                if flag.startswith("-march="):
                    flag = "-march=i686"
                ncxxflags.append(flag)
            self.build.cxxflags = ncxxflags

            self.build.host = "i686-pc-linux-gnu"

            # Get the multilib gcc stuff set up
            if self.spec.pkg_clang:
                self.build.cc = "clang -m32"
                self.build.cxx = "clang++ -m32"
            else:
                self.build.cc = "gcc -m32"
                self.build.cxx = "g++ -m32"

        # Set the $pkgfiles up properly
        spec_dir = os.path.dirname(os.path.abspath(self.spec.path))
        self.files_dir = os.path.join(spec_dir, "files")

        # We'll export job count ourselves..
        jobs = conf.values.build.jobs
        if "-j" in jobs:
            jobs = jobs.replace("-j", "")
        try:
            jcount = int(jobs)
            self.build.jobcount = jcount
        except Exception as e:
            console_ui.emit_warning("BUILD",
                                    "Invalid job count of {}, defaulting to 2".
                                    format(jobs))

        self.global_archive_dir = conf.values.dirs.archives_dir

    def enable_pgo_generate(self):
        """ Enable GPO generate step """
        pgo_dir = self.get_pgo_dir()
        self.build.cflags = Flags.pgo_gen_flags(self.build.cflags, pgo_dir)
        self.build.cxxflags = Flags.pgo_gen_flags(self.build.cxxflags, pgo_dir)

    def enable_pgo_use(self):
        """ Enable PGO use step """
        pgo_dir = self.get_pgo_dir()
        self.build.cflags = Flags.pgo_use_flags(self.build.cflags, pgo_dir)
        self.build.cxxflags = Flags.pgo_use_flags(self.build.cxxflags, pgo_dir)

    def clean_pgo(self):
        suffixes = ["pgo", "pgo-32"]
        pgo_dirs = [os.path.abspath("{}/root/{}/{}".format(
                    self.get_build_prefix(),
                    self.spec.pkg_name, x)) for x in suffixes]

        for d in pgo_dirs:
            if not os.path.exists(d):
                continue
            try:
                shutil.rmtree(d)
            except Exception as e:
                console_ui.emit_error("Build", "Failed to clean PGO dir")
                print(e)
                return False
        return True

    def clean_install(self):
        """ Purge the install directory """
        d = self.get_install_dir()
        if not os.path.exists(d):
            return True
        try:
            shutil.rmtree(d)
        except Exception as e:
            print(e)
            return False
        return True

    def clean_pkg(self):
        """ Purge the packing directory """
        d = self.get_packaging_dir()
        if not os.path.exists(d):
            return True
        try:
            shutil.rmtree(d)
        except Exception as e:
            print(e)
            return False
        return True
