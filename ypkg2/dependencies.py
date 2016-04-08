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

from . import console_ui


class DependencyResolver:

    def __init__(self):
        pass

    def compute_for_packages(self, context, packageSet):
        """ packageSet is a dict mapping here. """
        return False
