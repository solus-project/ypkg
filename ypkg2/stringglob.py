#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Re-adapted into ypkg2 from autospec
#
#  Copyright (C) 2016 Intel Corporation
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#

import fnmatch


class StringPathGlob:

    pattern = None
    prefixMatch = False
    priority = 0

    def __init__(self, pattern, prefixMatch=False, priority=0):
        self.pattern = pattern
        self.prefixMatch = prefixMatch
        self.priority = priority
        self.tag = tag

    @staticmethod
    def is_a_pattern(item):
        if "[" in item or "?" in item or "*" in item:
            return True
        return False

    def match(self, path):
        if self.prefixMatch:
            if self.pattern.endswith(os.sep) and not
            StringPathGlob.is_a_pattern(self.pattern):
                if path.startswith(self.pattern):
                    return True
            return False

        our_splits = self.pattern.split(os.sep)
        test_splits = path.split(os.sep)

        their_len = len(test_splits)
        our_len = len(our_splits)

        if our_len > their_len:
            return False

        for i in range(0, our_len):
            our_elem = our_splits[i]
            their_elem = test_splits[i]

            if our_elem == their_elem:
                continue

            if StringPathGlob.is_a_pattern(our_elem):
                if not fnmatch.fnmatchcase(their_elem, our_elem):
                    return False
            else:
                return False

        return True

    def __str__(self):
        return str(self.pattern)

    def __eq__(self, obj2):
        return self.pattern == obj2.pattern

    def __ne__(self, obj):
        return not(self == obj)

    def __hash__(self):
        return hash((self.pattern, self.priority))

    def getPattern(self):
        return self.pattern
