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

import os

from yaml import load as yaml_load
try:
    from yaml import CLoader as Loader
except Exception as e:
    console_ui.emit_warning("YAML", "Native YAML loader unavailable")
    from yaml import Loader


class YpkgSpec:

    def __init__(self):
        pass

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

        console_ui.emit_info("TODO", "Parsing not yet implemented")

        with open(path, "r") as inpfile:
            try:
                yaml_data = yaml_load(inpfile, Loader=Loader)
            except Exception as e:
                console_ui.emit_error("Parse", "Failed to parse YAML file")
                print(e)
                return False

        return False
