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

import yaml
import os
import sys
import re
from collections import OrderedDict

iterable_types = [list, dict]


class OneOrMoreString:
    """ Request one or more string """
    def __init__(self):
        pass


class MultimapFormat:
    """ Request items in a multimap format """

    ref_object = None
    ref_function = None
    ref_default = None

    def __init__(self, ref_object, ref_function, ref_default):
        self.ref_object = ref_object
        self.ref_function = ref_function
        self.ref_default = unicode(ref_default)


def _insert_helper(mapping, key, value):
    """ Helper to prevent repetetive code """
    if key not in mapping:
        mapping[key] = list()
    mapping[key].append(value)


def get_key_value_mapping(data, t):
    mapping = OrderedDict()

    dicts = filter(lambda s: isinstance(s, dict), data)
    no_keys = filter(lambda s: type(s) not in iterable_types, data)

    for key in no_keys:
        _insert_helper(mapping, t.ref_default, key)

    # Explicit key: to value mapping
    for mapp in dicts:
        keys = mapp.keys()
        if len(keys) > 1:
            console_ui.emit_error("YAML",
                                  "Encountered multiple keys")
            return False
        key = keys[0]
        val = mapp[key]

        if isinstance(val, list):
            bad = filter(lambda s: type(s) in iterable_types, val)
            if len(bad) > 0:
                console_ui.emit_error("YAML",
                                      "Multimap does not support inception...")
                return None
            for item in val:
                _insert_helper(mapping, key, unicode(item))
            continue
        elif type(val) in iterable_types:
            # Illegal to have a secondary layer here!!
            console_ui.emit_error("YAML", "Expected a value here")
            print("Erronous line: {}".format(str(mapp)))
            return None
        else:
            # This is key->value mapping
            _insert_helper(mapping, key, unicode(val))

    return mapping


def assertMultimap(ymlFile, key, t):
    """ Perform multi-map operations in the given key """

    if key not in ymlFile:
        console_ui.emit_error("YAML:{}".format(key),
                              "Fatally requested a non-existent key!")
        return False

    val = ymlFile[key]
    if type(val) not in iterable_types:
        mapping = get_key_value_mapping([unicode(val)], t)
    else:
        mapping = get_key_value_mapping(ymlFile[key], t)

    if mapping is None:
        return False

    for key in mapping.keys():
        dat = mapping[key]
        for val in dat:
            t.ref_function(unicode(key), unicode(val))

    return True


def assertGetType(ymlFile, key, t):
    """ Ensure a value of the given type exists """
    if key not in ymlFile:
        console_ui.emit_error("YAML",
                              "Mandatory token '{}' is missing".format(key))
        return None
    val = ymlFile[key]
    val_type = type(val)
    # YAML might report integer when we want strings, which is OK.

    if t == OneOrMoreString:
        ret = list()
        if val_type == str or val_type == unicode:
            ret.append(val)
            return ret
        if val_type != list:
            console_ui.emit_error("YAML:{}".format(key),
                                  "Token must be a string or list of strings")
            return None
        for item in val:
            if type(item) in iterable_types:
                console_ui.emit_error("YAML:{}".format(key),
                                      "Found unexpected iterable type in list")
                console_ui.emit_error("YAML:{}".format(key),
                                      "Expected a string")
                return None
            ret.append(item)
        return ret

    if t == str:
        if type(val) not in iterable_types:
            val = str(val)
    elif t == unicode:
        if type(val) not in iterable_types:
            val = unicode(val)

    if not isinstance(val, t):
        j = t.__name__
        f = type(val).__name__
        console_ui.emit_error("YAML",
                              "Token '{}' must be of type '{}'".format(key, j))
        console_ui.emit_error("YAML:{}".format(key),
                              "Token found was of type '{}".format(f))
        return None
    return val
