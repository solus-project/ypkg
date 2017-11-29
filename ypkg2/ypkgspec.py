#!/bin/true
# -*- coding: utf-8 -*-
#
#  This file is part of ypkg2
#
#  Copyright 2015-2017 Ikey Doherty <ikey@solus-project.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#

from . import console_ui
from . import yamlhelper

from .yamlhelper import OneOrMoreString, MultimapFormat
from .sources import SourceManager, GitSource

import os
from collections import OrderedDict
# Consider moving this into a stub
import pisi.version
import pisi.history
import pisi.pxml.xmlfile as xmlfile
import pisi.pxml.autoxml as autoxml

from yaml import load as yaml_load
try:
    from yaml import CLoader as Loader
except Exception as e:
    console_ui.emit_warning("YAML", "Native YAML loader unavailable")
    from yaml import Loader


class PackageSanity:

    @staticmethod
    def is_name_valid(name):
        """ Determine if a package name is actually valid. """
        name = str(name.strip())
        if len(name) < 1:
            console_ui.emit_error("YAML:name",
                                  "Package name cannot be empty")
            return False

        if " " in name:
            console_ui.emit_error("YAML:name",
                                  "Package names cannot contain whitespace")
            return False
        illegal = set()
        permitted = ['-', '_', '+', '.']
        for char in name[0:]:
            if char in permitted:
                continue
            if not char.isalpha() and not char.isdigit():
                illegal.add(char)
        if len(illegal) == 0:
            return True

        console_ui.emit_error("YAML:name",
                              "Illegal characters in package name '{}' : {}".
                              format(name, ", ".join(illegal)))
        return False

    @staticmethod
    def is_version_valid(version):
        """ Determine if the given version is valid """
        try:
            v = pisi.version.make_version(version)
        except Exception as e:
            console_ui.emit_error("YAML", "Invalid version: {}".format(
                                   version))
            return False
        return True


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
    pkg_debug = True
    pkg_clang = False
    pkg_strip = True
    pkg_ccache = True
    pkg_emul32 = False
    pkg_avx2 = False
    pkg_autodep = True
    pkg_extract = True
    pkg_optimize = None
    pkg_libsplit = True

    # Only used by solbuild
    pkg_networking = False

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
    step_profile = None

    # More meta
    summaries = None
    descriptions = None
    rundeps = None
    components = None

    # Multimap: replaces/conflicts
    replaces = None
    conflicts = None

    # Path to filename
    path = None

    # Permanent paths
    pkg_permanent = None

    # Custom user provided patterns
    patterns = None

    history = None

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

    def add_pattern(self, key, pt):
        if key not in self.patterns:
            self.patterns[key] = list()
        if pt in self.patterns[key]:
            console_ui.emit_warning("YAML", "Duplicate pattern: {}".format(pt))
        self.patterns[key].append(pt)

    def add_replace(self, key, val):
        """ Add a 'replaces:' to the package """
        if key not in self.replaces:
            self.replaces[key] = list()
        # i.e. llvm-clang-devel replaces clang-devel
        if val in self.replaces and val != key:
            console_ui.emit_warning("YAML",
                                    "Duplicate replace: {}".format(val))
            return
        self.replaces[key].append(val)

    def add_conflict(self, key, val):
        """ Add a 'conflicts:' to the package """
        if key not in self.conflicts:
            self.conflicts[key] = list()
        if val in self.conflicts:
            console_ui.emit_warning("YAML",
                                    "Duplicate conflict: {}".format(val))
            return
        self.conflicts[key].append(val)

    def __init__(self):
        # These tokens *must* exist
        self.mandatory_tokens = OrderedDict([
            ("name", str),
            ("version", str),
            ("release", int),
            ("license", OneOrMoreString),
            ("summary", MultimapFormat(self, self.add_summary, "main")),
            ("description", MultimapFormat(self, self.add_desc, "main")),
            ("source", list),  # We verify sources later
        ])
        # These guys are optional
        self.optional_tokens = OrderedDict([
            ("homepage", str),
            ("devel", bool),
            ("clang", bool),
            ("debug", bool),
            ("strip", bool),
            ("ccache", bool),
            ("emul32", bool),
            ("networking", bool),
            ("avx2", bool),
            ("autodep", bool),
            ("extract", bool),
            ("libsplit", bool),
            ("patterns", MultimapFormat(self, self.add_pattern, "main")),
            ("permanent", OneOrMoreString),
            ("builddeps", OneOrMoreString),
            ("rundeps", MultimapFormat(self, self.add_rundep, "main")),
            ("component", MultimapFormat(self, self.add_component, "main")),
            ("conflicts", MultimapFormat(self, self.add_conflict, "main")),
            ("replaces", MultimapFormat(self, self.add_replace, "main")),
            ("optimize", OneOrMoreString),
        ])
        # Build steps are handled separately
        self.build_steps = OrderedDict([
            ("setup", unicode),
            ("build", unicode),
            ("install", unicode),
            ("check", unicode),
            ("profile", unicode),
        ])
        self.summaries = dict()
        self.descriptions = dict()
        self.rundeps = dict()
        self.components = dict()
        self.patterns = OrderedDict()
        self.replaces = dict()
        self.conflicts = dict()

    def init_defaults(self):
        # Add some sane defaults
        name = self.pkg_name
        if "devel" not in self.summaries:
            self.add_summary("devel", "Development files for {}".format(name))
        if "32bit" not in self.summaries:
            self.add_summary("32bit", "32-bit libraries for {}".format(name))
        if "32bit-devel" not in self.summaries:
            self.add_summary("32bit-devel", "Development files for 32-bit {}".
                             format(name))

        if "devel" not in self.components:
            if self.pkg_devel:
                self.add_component("devel", "system.devel")
            else:
                self.add_component("devel", "programming.devel")
        if "32bit" not in self.components:
            self.add_component("32bit", "emul32")
        if "32bit-devel" not in self.components:
            self.add_component("32bit-devel", "programming.devel")
        if "docs" not in self.components:
            self.add_component("docs", "programming.docs")

        # debuginfos
        if "dbginfo" not in self.components:
            self.add_component("dbginfo", "debug")
        if "dbginfo" not in self.summaries:
            self.add_summary("dbginfo", "Debug symbols for {}".format(name))
        if "32bit-dbginfo" not in self.components:
            self.add_component("32bit-dbginfo", "debug")
        if "32bit-dbginfo" not in self.summaries:
            self.add_summary("32bit-dbginfo", "32-bit debug symbols for {}"
                             .format(name))
        if "docs" not in self.summaries:
            self.add_summary("docs", "Documentation for {}".format(name))

        extras = []
        if self.pkg_emul32:
            extras.extend(["glibc-32bit-devel", "libgcc-32bit",
                           "libstdc++-32bit", "fakeroot-32bit"])
            if self.pkg_clang:
                extras.extend(["llvm-clang-32bit", "llvm-clang-32bit-devel"])
        if self.pkg_clang:
            extras.extend(["llvm-clang", "llvm-clang-devel"])
        if self.pkg_optimize:
            if "thin-lto" in self.pkg_optimize:
                extras.extend(["binutils-gold"])

        man = SourceManager()
        try:
            man.identify_sources(self)
            for x in man.sources:
                if isinstance(x, GitSource):
                    extras.append("git")
                    break
        except:
            pass
        for x in extras:
            if not self.pkg_builddeps:
                self.pkg_builddeps = list()
            if x not in self.pkg_builddeps:
                self.pkg_builddeps.append(x)

    def load_from_path(self, path):
        self.path = path
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

        b = self.load_from_data(yaml_data)
        if not b:
            return b
        return self.load_component()

    def load_from_data(self, yaml_data):
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

        # Validate the names and version
        if not PackageSanity.is_version_valid(self.pkg_version):
            return False
        if not PackageSanity.is_name_valid(self.pkg_name):
            return False

        for name in self.patterns:
            fname = self.get_package_name(name)
            if not PackageSanity.is_name_valid(fname):
                return False

        self.init_defaults()

        return True

    def load_history(self, path):
        try:
            self.history = PackageHistory()
            self.history.read(path)
            up = self.history.history[0]
            release = int(up.release)
            version = up.version

            if release != self.pkg_release:
                console_ui.emit_warning("HISTORY", "Release not consistent")
            if version != self.pkg_version:
                console_ui.emit_warning("HISTORY", "Version not consistent..")
        except Exception as e:
            console_ui.emit_error("HISTORY", "Could not load history file")
            print(e)
            return False
        return True

    def load_component(self):
        if "main" in self.components:
            return True

        p = os.path.dirname(self.path)

        for i in ["component.xml", "../component.xml"]:
            fpath = os.path.join(p, i)
            if not os.path.exists(fpath):
                continue
            comp = pisi.component.CompatComponent()
            try:
                comp.read(fpath)
                console_ui.emit_error("Component",
                                      "Using legacy component.xml: {}".
                                      format(fpath))
                print("  Please switch to using the 'component' key")
                return False
            except Exception as e:
                console_ui.emit_error("Component", "Error in legacy file")
                print(e)
                return False
        return True

    def get_package_name(self, name):
        if name == "main":
            return self.pkg_name
        if name.startswith('^'):
            return str(name[1:])
        return "{}-{}".format(self.pkg_name, name)

    def get_component(self, name):
        if name in self.components:
            return self.components[name]
        return None

    def get_description(self, name):
        if name not in self.descriptions:
            return self.descriptions["main"]
        return self.descriptions[name]

    def get_summary(self, name):
        if name not in self.summaries:
            return self.summaries["main"]
        return self.summaries[name]


class PackageHistory(xmlfile.XmlFile):

    __metaclass__ = autoxml.autoxml

    tag = "YPKG"

    t_History = [[pisi.specfile.Update], autoxml.mandatory]
