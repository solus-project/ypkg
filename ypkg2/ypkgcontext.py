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


class BuildConfig:

    arch = None
    host = None
    ccache = None

    cflags = None
    cxxflags = None
    ldflags = None


class YpkgContext:
    """ Base context for things like cflags, etc """

    build = None

    global_archive_dir = None

    def __init__(self):
        self.build = BuildConfig()
        self.init_config()

    def init_config(self):
        conf = pisi.config.Config()

        # For now follow the eopkg.conf..
        self.build.host = conf.values.build.host
        self.build.arch = conf.values.build.arch
        self.build.cflags = set(conf.values.build.cflags.split(" "))
        self.build.cxxflags = set(conf.values.build.cxxflags.split(" "))
        self.build.ldflags = set(conf.values.build.ldflags.split(" "))
        self.build.ccache = "ccache" in conf.values.build.buildhelper

        self.global_archive_dir = conf.values.dirs.archives_dir
