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
import shutil
import tempfile
import subprocess


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

    build_package(args.filename)


def clean_build_dirs(context):
    if os.path.exists(context.get_build_dir()):
        try:
            shutil.rmtree(context.get_build_dir())
        except Exception as e:
            console_ui.emit_error("BUILD", "Could not clean build directory")
            print(e)
            return False
    return True


def execute_step(context, step, step_n, work_dir):
    script = ScriptGenerator(context, context.spec, work_dir)

    exports = script.emit_exports()

    # Run via bash with enable and error
    full_text = "#!/bin/bash\nset -e\nset -x\n"
    # cd to the given directory
    full_text += "\n\ncd \"%workdir%\"\n"

    # Add our exports
    full_text += "\n".join(exports)
    full_text += "\n\n{}\n".format(step)
    output = script.escape_string(full_text)

    with tempfile.NamedTemporaryFile(prefix="ypkg-%s" % step_n) as script_ex:
        script_ex.write(output)
        script_ex.flush()

        cmd = ["/bin/bash", script_ex.name]
        try:
            subprocess.check_call(cmd, stdin=subprocess.PIPE)
        except Exception as e:
            print(e)
            return False
    return True


def build_package(filename):
    """ Will in future be moved to a separate part of the module """
    spec = YpkgSpec()
    if not spec.load_from_path(filename):
        print("Unable to continue - aborting")
        sys.exit(1)

    manager = SourceManager()
    if not manager.identify_sources(spec):
        print("Unable to continue - aborting")
        sys.exit(1)

    # Dummy content
    console_ui.emit_info("Info", "Building {}-{}".
                         format(spec.pkg_name, spec.pkg_version))

    ctx = YpkgContext(spec)

    need_verify = []
    for src in manager.sources:
        if src.cached(ctx):
            need_verify.append(src)
            continue
        if not src.fetch(ctx):
            console_ui.emit_error("Source", "Cannot continue without sources")
            sys.exit(1)
        need_verify.append(src)

    for verify in need_verify:
        if not verify.verify(ctx):
            console_ui.emit_error("Source", "Cannot verify sources")
            sys.exit(1)

    if not clean_build_dirs(ctx):
        sys.exit(1)

    # Only ever extract the primary source ourselves
    if spec.pkg_extract:
        src = manager.sources[0]
        if not src.extract(ctx):
            console_ui.emit_error("Source", "Cannot extract sources")
            sys.exit(1)

    steps = {
        'setup': spec.step_setup,
        'build': spec.step_build,
        'install': spec.step_install,
        'check': spec.step_check
    }

    work_dir = manager.get_working_dir(ctx)
    if not work_dir:
        sys.exit(1)

    for step_name in steps:
        step = steps[step_name]
        if not step:
            continue
        console_ui.emit_info("Build", "Running step: {}".format(step_name))

        if execute_step(ctx, step, step_name, work_dir):
            console_ui.emit_success("Build", "{} successful".format(step_name))
            continue
        console_ui.emit_error("Build", "{} failed".format(step_name))
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
