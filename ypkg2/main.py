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

from ui import YpkgUI
import sys
import argparse


def show_version():
    print("Ypkg - Package Build Tool")
    print("\nCopyright (C) 2015-2016 Ikey Doherty\n")
    print("This program is free software; you are free to redistribute it\n"
          "and/or modify it under the terms of the GNU General Public License"
          "\nas published by the Free Software foundation; either version 2 of"
          "\nthe License, or (at your option) any later version.")
    sys.exit(0)


def main():
    ui = YpkgUI()

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
        ui.allow_colors = False
    # Show version
    if args.version:
        show_version()

    # Grab filename
    if not args.filename:
        ui.emit_error("Error", "Please provide a filename to ypkg")
        print("")
        parser.print_help()
        sys.exit(1)

    # So yeah we do nothing yet.
    ui.emit_warning("Warning", "Not yet implemented")

    sys.exit(0)

if __name__ == "__main__":
    main()
