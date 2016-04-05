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
from .ypkgspec import YpkgSpec
from .sources import SourceManager
from .ypkgcontext import YpkgContext
from .scripts import ScriptGenerator
from .packages import PackageGenerator

import sys
import argparse
import os


def show_version():
    print("Ypkg - Package Build Tool")
    print("\nCopyright (C) 2015-2016 Ikey Doherty\n")
    print("This program is free software; you are free to redistribute it\n"
          "and/or modify it under the terms of the GNU General Public License"
          "\nas published by the Free Software foundation; either version 2 of"
          "\nthe License, or (at your option) any later version.")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="Ypkg Package Build Tool")
    parser.add_argument("-n", "--no-colors", help="Disable color output",
                        action="store_true")
    parser.add_argument("-v", "--version", action="store_true",
                        help="Show version information and exit")
    # Main file
    parser.add_argument("filename", help="Path to the ypkg YAML file to build",
                        nargs='?')

    args = parser.parse_args()
    # Kill colors
    if args.no_colors:
        console_ui.allow_colors = False
    # Show version
    if args.version:
        show_version()

    # Grab filename
    if not args.filename:
        console_ui.emit_error("Error", "Please provide a filename to ypkg")
        print("")
        parser.print_help()
        sys.exit(1)

    # Attempt to parse the Ypkg file and ensure that it's sane.
    spec = YpkgSpec()
    if not spec.load_from_path(args.filename):
        print("Unable to continue - aborting")
        sys.exit(1)

    # Dummy content
    print("Parsing package {} - version {}".format(
          spec.pkg_name, spec.pkg_version))
    if spec.pkg_homepage:
        print("Homepage: {}".format(spec.pkg_homepage))

    # Further testing
    print("Summary: {}\nDescription: {}".format(spec.summaries["main"],
                                                spec.descriptions["main"]))

    manager = SourceManager()
    if not manager.identify_sources(spec):
        print("Unable to continue - aborting")
        sys.exit(1)

    ctx = YpkgContext(spec)
    # Literally just testing.
    scr = ScriptGenerator(ctx, spec)

    script = "{}\n{}\n{}\n".format(
        spec.step_setup, spec.step_build, spec.step_install)
    print(scr.escape_string(script))

    sys.exit(0)

if __name__ == "__main__":
    main()
