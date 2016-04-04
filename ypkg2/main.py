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


def main():
    ui = YpkgUI()

    ui.emit_error("Error", "Not yet implemented")
    ui.emit_warning("Warning", "Not yet implemented")
    ui.emit_info("Info", "Not yet implemented")
    ui.emit_success("Success", "Not yet implemented")

    sys.exit(0)

if __name__ == "__main__":
    main()
