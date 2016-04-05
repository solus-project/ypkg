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
from . import yamlhelper

from yamlhelper import OneOrMoreString, MultimapFormat

import os
from collections import OrderedDict

from yaml import load as yaml_load
try:
    from yaml import CLoader as Loader
except Exception as e:
    console_ui.emit_warning("YAML", "Native YAML loader unavailable")
    from yaml import Loader


class YpkgSpec:

    # Root meta information
    pkg_name = None
    pkg_version = None
    pkg_release = None
    pkg_homepage = None
    pkg_license = None
    pkg_source = None

    # Build control
    pkg_devel = False
    pkg_clang = False
    pkg_strip = True
    pkg_ccache = True
    pkg_emul32 = False
    pkg_autodep = True
    pkg_extract = True

    # Dependencies
    pkg_builddeps = None

    mandatory_tokens = None
    optional_tokens = None
    build_steps = None

    # Build steps
    step_setup = None
    step_build = None
    step_install = None
    step_check = None

    summaries = None
    descriptions = None
    rundeps = None
    components = None

    def add_summary(self, key, value):
        """ Add a summary to a package """
        self.summaries[key] = value

    def add_desc(self, key, value):
        """ Add a description to a package """
        self.descriptions[key] = value

    def add_rundep(self, key, val):
        if key not in self.rundeps:
            self.rundeps[key] = list()
        if val in self.rundeps[key]:
            console_ui.emit_warning("YAML", "Duplicate rundep: {}".format(val))
            return
        self.rundeps[key].append(val)

    def add_component(self, key, value):
        """ Set the component for a package """
        self.components[key] = value

    def __init__(self):
        # These tokens *must* exist
        self.mandatory_tokens = OrderedDict([
            ("name", unicode),
            ("version", unicode),
            ("release", int),
            ("license", OneOrMoreString),
            ("summary", MultimapFormat(self, self.add_summary, "main")),
            ("description", MultimapFormat(self, self.add_desc, "main")),
            ("source", list),  # We verify sources later
        ])
        # These guys are optional
        self.optional_tokens = OrderedDict([
            ("homepage", unicode),
            ("devel", bool),
            ("clang", bool),
            ("strip", bool),
            ("ccache", bool),
            ("emul32", bool),
            ("autodep", bool),
            ("extract", bool),
            ("builddeps", OneOrMoreString),
            ("rundeps", MultimapFormat(self, self.add_rundep, "main")),
            ("component", MultimapFormat(self, self.add_component, "main")),
        ])
        # Build steps are handled separately
        self.build_steps = OrderedDict([
            ("setup", unicode),
            ("build", unicode),
            ("install", unicode),
            ("check", unicode),
        ])
        self.summaries = dict()
        self.descriptions = dict()
        self.rundeps = dict()
        self.components = dict()

    def load_from_path(self, path):
        if not os.path.exists(path):
            console_ui.emit_error("Error", "Path does not exist")
            return False
        if not os.path.isfile and not os.path.islink(path):
            console_ui.emit_error("Error", "File specified is not a file")
            return False

        filename = os.path.basename(path)

        # We'll get rid of this at some point :P
        if filename != "package.yml":
            console_ui.emit_warning("Unnecessarily Anal Warning",
                                    "File is not named package.yml")

        # Attempt to parse the input file
        with open(path, "r") as inpfile:
            try:
                yaml_data = yaml_load(inpfile, Loader=Loader)
            except Exception as e:
                console_ui.emit_error("YAML", "Failed to parse YAML file")
                print(e)
                return False

        # Grab the main root elements (k->v mapping)
        sets = [self.mandatory_tokens, self.optional_tokens, self.build_steps]
        for tk_set in sets:
            for token in tk_set.keys():
                t = tk_set[token]

                if token not in yaml_data and tk_set != self.mandatory_tokens:
                    # ok to skip optionals
                    continue

                if isinstance(t, MultimapFormat):
                    if not yamlhelper.assertMultimap(yaml_data, token, t):
                        return False
                    continue
                else:
                    val = yamlhelper.assertGetType(yaml_data, token, t)
                if val is None:
                    return False
                # Handle build steps differently to avoid collisions
                if tk_set == self.build_steps:
                    instance_name = "step_{}".format(token)
                else:
                    instance_name = "pkg_{}".format(token)
                if not hasattr(self, instance_name):
                    console_ui.emit_error("YAML:{}".format(token),
                                          "Internal error for unknown token")
                    return False
                setattr(self, instance_name, val)

        if "main" not in self.summaries:
            console_ui.emit_info("YAML", "Missing summary for package")
            return False
        if "main" not in self.descriptions:
            console_ui.emit_info("YAML", "Missing description for package")
            return False

        # Ensure this package would actually be able to build..
        steps = [self.step_setup, self.step_build, self.step_install]
        steps = filter(lambda s: s, steps)
        if len(steps) == 0:
            console_ui.emit_error("YAML", "No functional build steps found")
            return False

        return True
