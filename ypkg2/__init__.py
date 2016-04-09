#!/bin/true
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

from .ui import YpkgUI

import re


global console_ui

console_ui = YpkgUI()


def remove_prefix(fpath, prefix):
    if fpath.startswith(prefix):
        fpath = fpath[len(prefix)+1:]
    if fpath[0] != '/':
        fpath = "/" + fpath
    return fpath

pkgconfig32_dep = re.compile("^pkgconfig32\((.*)\)$")
pkgconfig_dep = re.compile("^pkgconfig\((.*)\)$")
