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

from collections import OrderedDict
import re


class ScriptGenerator:
    """ Generates build scripts on the fly by providing a default header
        tailored to the current build context and performing substitution
        on exported macros from this instance """

    macros = None
    context = None

    def __init__(self, context):
        self.macros = OrderedDict()
        self.context = context
        self.init_default_macros()

    def define_macro(self, key, value):
        """ Define a named macro. This will take the form %name% """
        self.macros["%{}%".format(key)] = value

    def define_action_macro(self, key, value):
        """ Define an action macro. These take the form %action """
        self.macros["%{}".format(key)] = value

    def init_default_macros(self):

        # Until we get more clever, this is /usr/lib64
        libdir = "lib64"
        self.define_macro("libdir", "/usr/{}".format(libdir))
        self.define_macro("installroot", None)  # FIXME
        self.define_macro("workdir", None)      # FIXME
        self.define_macro("JOBS", "-j{}".format(self.context.build.jobcount))

        self.define_action_macro("configure", "./configure $CONFOPTS")
        self.define_action_macro("make", "make %JOBS%")
        self.define_action_macro("make_install",
                                 "%make install DESTDIR=%installroot%")
        self.define_action_macro("patch",
                                 "patch -t -E --no-backup-if-mismatch -f")

    def escape_string(self, input_string):
        """ Recursively escape our macros out of a string until no more of our
            macros appear in it """
        op = str(input_string)

        keys = self.macros.keys()
        keys.reverse()

        while (True):
            found = False
            removals = set()
            for macro in keys:
                if macro in op:
                    found = True
                repla = self.macros[macro]
                if repla is None:
                    # Handle undefined symbols
                    repla = ""
                if macro not in op:
                    removals.add(macro)
                    continue
                tmp = r"({})\b".format(str(macro))
                op = re.sub(tmp, repla, op)
                if macro in op:
                    tmp = r"({})".format(str(macro))
                    op = re.sub(tmp, repla, op)
                if macro not in op:
                    removals.add(macro)
                    continue
            if not found:
                break
            for removal in removals:
                keys.remove(removal)

        return op
