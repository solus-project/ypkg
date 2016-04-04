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


class AnsiColors:
    """ ANSI sequences for color output """

    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    LGREY = '\033[37m'
    DGREY = '\033[90m'
    LRED = '\033[91m'
    LGREEN = '\033[92m'
    LYELLOW = '\033[93m'
    LBLUE = '\033[94m'
    LMAGENTA = '\033[95m'
    LCYAN = '\033[96m'
    WHITE = '\033[97m'

    RESET = '\033[0m'

    BOLD = '\033[1m'
    UNBOLD = '\033[21m'

    DIM = '\033[2m'
    UNDIM = '\033[22m'

    UNDERLINE = '\033[4m'
    UNUNDERLINE = '\033[24m'

    BLINK = '\033[5m'
    UNBLINK = '\033[25m'

    REVERSE = '\033[7m'
    UNREVERSE = '\033[27m'

    HIDEEN = '\033[8m'
    UNHIDDEN = '\033[28m'


class YpkgUI:

    """ We must allow toggling of colors in the UI """
    allow_colors = False

    def __init__(self):
        self.allow_colors = True

    def emit_error(self, key, error):
        """ Report an error to the user """
        if not self.allow_colors:
            print("[{}] {}".format(key, error))
        else:
            print("{}[{}]{} {}{}{}".format(AnsiColors.RED, key,
                  AnsiColors.RESET, AnsiColors.BOLD, error, AnsiColors.RESET))

    def emit_warning(self, key, error):
        """ Report a warning to the user """
        if not self.allow_colors:
            print("[{}] {}".format(key, error))
        else:
            print("{}[{}]{} {}{}{}".format(AnsiColors.YELLOW, key,
                  AnsiColors.RESET, AnsiColors.BOLD, error, AnsiColors.RESET))

    def emit_info(self, key, error):
        """ Report information to the user """
        if not self.allow_colors:
            print("[{}] {}".format(key, error))
        else:
            print("{}[{}]{} {}{}{}".format(AnsiColors.LBLUE, key,
                  AnsiColors.RESET, AnsiColors.BOLD, error, AnsiColors.RESET))

    def emit_success(self, key, error):
        """ Report success to the user """
        if not self.allow_colors:
            print("[{}] {}".format(key, error))
        else:
            print("{}[{}]{} {}{}{}".format(AnsiColors.GREEN, key,
                  AnsiColors.RESET, AnsiColors.BOLD, error, AnsiColors.RESET))
