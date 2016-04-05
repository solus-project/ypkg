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

import pisi.config

# These flag sets are courtesy of autospec in
# Clear Linux Project For Intel Architecture
SPEED_FLAGS = "-flto -ffunction-sections -fno-semantic-interposition -O3"
SIZE_FLAGS = "-Os -ffunction-sections"
PGO_GEN_FLAGS = "-fprofile-generate -fprofile-dir=pgo"
PGO_USE_FLAGS = "-fprofile-use -fprofile-dir=pgo -fprofile-correction"


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
        return newflags

    @staticmethod
    def pgo_gen_flags(f):
        """ Update flags with PGO generator flags """
        r = set(f)
        r.update(PGO_GEN_FLAGS.split(" "))
        return r

    @staticmethod
    def pgo_use_flags(f):
        """ Update flags with PGO use flags """
        r = set(f)
        r.update(PGO_USE_FLAGS.split(" "))
        return r


class BuildConfig:

    arch = None
    host = None
    ccache = None

    cflags = None
    cxxflags = None
    ldflags = None

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

    def __init__(self):
        self.build = BuildConfig()
        self.init_config()

    def init_config(self):
        """ Initialise our configuration prior to building """
        conf = pisi.config.Config()

        # For now follow the eopkg.conf..
        self.build.host = conf.values.build.host
        self.build.arch = conf.values.build.arch
        self.build.cflags = set(conf.values.build.cflags.split(" "))
        self.build.cxxflags = set(conf.values.build.cxxflags.split(" "))
        self.build.ldflags = set(conf.values.build.ldflags.split(" "))
        self.build.ccache = "ccache" in conf.values.build.buildhelper

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
