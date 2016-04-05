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
    spec = None

    def __init__(self, context, spec):
        self.macros = OrderedDict()
        self.context = context
        self.spec = spec
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

        self.define_action_macro("configure", "./configure %CONFOPTS%")
        self.define_action_macro("make", "make %JOBS%")
        self.define_action_macro("make_install",
                                 "%make install DESTDIR=\"%installroot%\"")
        self.define_action_macro("patch",
                                 "patch -t -E --no-backup-if-mismatch -f")

        # Consider moving this somewhere else
        self.define_macro("CFLAGS", self.context.build.cflags)
        self.define_macro("CXXFLAGS", self.context.build.cxxflags)
        self.define_macro("LDFLAGS", self.context.build.ldflags)

        # Make this conditional depending on emul32 in context
        prefix = "/usr"
        host = self.context.build.host
        name = self.spec.pkg_name
        conf_ops = (prefix, host, libdir, libdir, name)

        self.define_macro("CONFOPTS",
                          "--prefix=%s --build=%s --libdir=/usr/%s "
                          "--mandir=/usr/share/man --infodir=/usr/share/man "
                          "--datadir=/usr/share/ --sysconfdir=/etc "
                          "--localstatedir=/var --libexecdir=/usr/%s/%s"
                          % conf_ops)

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
