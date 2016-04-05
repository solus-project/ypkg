#!/usr/bin/env python
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

from collections import OrderedDict
import re
import os

from yaml import load as yaml_load
try:
    from yaml import CLoader as Loader
except Exception as e:
    from yaml import Loader


class ScriptGenerator:
    """ Generates build scripts on the fly by providing a default header
        tailored to the current build context and performing substitution
        on exported macros from this instance """

    macros = None
    context = None
    spec = None

    def __init__(self, context, spec):
        self.macros = OrderedDict()
        self.context = context
        self.spec = spec
        self.init_default_macros()
        self.load_system_macros()

    def define_macro(self, key, value):
        """ Define a named macro. This will take the form %name% """
        self.macros["%{}%".format(key)] = value

    def define_action_macro(self, key, value):
        """ Define an action macro. These take the form %action """
        self.macros["%{}".format(key)] = value

    def load_system_macros(self):
        path = os.path.join(os.path.dirname(__file__), "rc.yml")

        try:
            f = open(path, "r")
            yamlData = yaml_load(f, Loader=Loader)
            f.close()
        except Exception as e:
            console_ui.emit_error("SCRIPTS", "Cannot load system macros")
            print(e)
            return

        for section in ["defines", "actions"]:
            if section not in yamlData:
                continue
            v = yamlData[section]

            if not isinstance(v, list):
                console_ui.emit_error("rc.yml",
                                      "Expected list of defines in rc config")
                return
            for item in v:
                if not isinstance(item, dict):
                    console_ui.emit_error("rc.yml",
                                          "Expected key:value mapping in list")
                    return
                keys = item.keys()
                if len(keys) > 1:
                    console_ui.emit_error("rc.yml",
                                          "Expected one key in key:value")
                    return
                key = keys[0]
                value = item[key]
                if value.endswith("\n"):
                    value = value[:-1]
                value = value.strip()
                if section == "defines":
                    self.define_macro(key, unicode(value))
                else:
                    self.define_action_macro(key, unicode(value))

    def init_default_macros(self):

        # Until we get more clever, this is /usr/lib64
        libdir = "lib64"

        self.define_macro("LIBDIR", "/usr/{}".format(libdir))
        self.define_macro("LIBSUFFIX", "64")
        self.define_macro("installroot", self.context.get_install_dir())
        self.define_macro("workdir", None)      # FIXME
        self.define_macro("JOBS", "-j{}".format(self.context.build.jobcount))

        # Consider moving this somewhere else
        self.define_macro("CFLAGS", " ".join(self.context.build.cflags))
        self.define_macro("CXXFLAGS", " ".join(self.context.build.cxxflags))
        self.define_macro("LDFLAGS", " ".join(self.context.build.ldflags))

        self.define_macro("HOST", self.context.build.host)
        self.define_macro("PKGNAME", self.spec.pkg_name)
        self.define_macro("PREFIX", "/usr")
        self.define_macro("PKGFILES", self.context.files_dir)

    def is_valid_macro_char(self, char):
        if char.isalpha():
            return True
        if char == "_":
            return True

    def escape_single(self, line):
        offset = line.find('%')
        if offset < 0:
            return (line, False)

        tmp_name = "%"
        tmp_idx = 0
        for i in xrange(offset+1, len(line)):
            if line[i] == "%":
                tmp_name += "%"
                break
            if self.is_valid_macro_char(line[i]):
                tmp_name += line[i]
            else:
                break
        start = line[0:offset]
        remnant = line[offset+len(tmp_name):]
        # TODO: Change to is-valid-macro check and consume anyway
        if tmp_name in self.macros:
            mc = self.macros[tmp_name]
            if mc is None:
                mc = ""
            line = "%s%s%s" % (start, mc, remnant)
            return (line, True)
        else:
            line = "%s%s%s" % (start, tmp_name, remnant)
            return (line, False)

    def escape_string(self, input_string):
        """ Recursively escape our macros out of a string until no more of our
            macros appear in it """
        ret = []

        for line in input_string.split("\n"):
            while (True):
                (line, cont) = self.escape_single(line)
                if not cont:
                    ret.append(line)
                    break

        return "\n".join(ret)
