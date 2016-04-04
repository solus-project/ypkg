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
    pkg_homepage = None

    # Build control
    pkg_devel = False
    pkg_clang = False
    pkg_strip = True
    pkg_ccache = True
    pkg_emul32 = False

    mandatory_tokens = None
    optional_tokens = None

    def __init__(self):
        # These tokens *must* exist
        self.mandatory_tokens = OrderedDict([
            ("name", unicode),
            ("version", unicode),
        ])
        # These guys are optional
        self.optional_tokens = OrderedDict([
            ("homepage", unicode),
            ("devel", bool),
            ("clang", bool),
            ("strip", bool),
            ("ccache", bool),
            ("emul32", bool),
        ])

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
        for tk_set in [self.mandatory_tokens, self.optional_tokens]:
            for token in tk_set.keys():
                t = tk_set[token]
                if token not in yaml_data and tk_set == self.optional_tokens:
                    # ok to skip optionals
                    continue
                val = yamlhelper.assertGetType(yaml_data, token, t)
                if not val:
                    return False
                instance_name = "pkg_{}".format(token)
                if not hasattr(self, instance_name):
                    console_ui.emit_error("YAML",
                                          "Internal error for unknown token")
                    return False
                setattr(self, instance_name, val)

        console_ui.emit_info("TODO", "Parsing not yet completed")

        return True
