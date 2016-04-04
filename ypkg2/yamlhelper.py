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

iterable_types = [list, dict]


def assertGetType(ymlFile, key, t):
    ''' Ensure a value of the given type exists '''
    if key not in ymlFile:
        console_ui.emit_error("YAML",
                              "Mandatory token '{}' is missing".format(key))
        return None
    val = ymlFile[key]
    # YAML might report integer when we want strings, which is OK.
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


def assertGetString(y, n):
    ''' Ensure string value exists '''
    if n not in y:
        print "Required string '%s' missing" % n
        sys.exit(1)
    try:
        r = str(y[n])
    except:
        print "Key '%s' must be a string" % n
        sys.exit(1)
    return r


def assertGetInteger(y, n):
    ''' Ensure integer value exists '''
    if n not in y:
        print "Required integer '%s' missing" % n
        sys.exit(1)
    r = y[n]
    if not isinstance(r, int):
        print "Key '%s' must be a integer" % n
        sys.exit(1)
    return r


def assertIsString(y, n):
    ''' Ensure value is string if it exists '''
    if n not in y:
        return
    r = None
    try:
        r = str(y[n])
    except:
        print "Key '%s' must be a string" % n
        sys.exit(1)
    return r


def assertStringList(y, n):
    ''' Ensure value is either a list of strings, or a list
        Returned value is always a list of strings '''
    if n not in y:
        print "Required string '%s' missing" % n
        sys.exit(1)
    r = y[n]
    ret = list()
    if isinstance(r, str) or isinstance(r, unicode):
        ret.append(r)
    elif isinstance(r, list):
        for i in r:
            if not isinstance(i, str) and not isinstance(i, unicode):
                print "[%s] Item '%s' is not a string" % (n, i)
                sys.exit(1)
            ret.append(i)
    else:
        print "'%s' is neither a string or list of strings" % n
    return ret


def do_multimap(data, fname, func):
    ''' Crazy looking assumption based logic..
        Used currently for rundeps, and works in the following way...
        Provided data needs to be in a list format:
            - name
            - name

        Default mapping will place the value "name" as the key
            - name

        Default mapping places each value in this list with default key:
            - [name, name, name, name]

        Explicit key and value:
            - name: rundep
        '''
    if not isinstance(data, list):
        print "'%s' is not a valid list" % fname
        sys.exit(1)
    for item in data:
        if isinstance(item, str) or isinstance(item, unicode):
            # main package
            func(name, item)
        elif isinstance(item, list):
            for subitem in item:
                if not isinstance(
                        subitem,
                        str) and not isinstance(
                        subitem,
                        unicode):
                    print "'%s' is not a valid string" % v
                    sys.exit(1)
                func(name, subitem)
        elif isinstance(item, dict):
            key = item.keys()
            val = item.values()
            if len(key) != 1 or len(val) != 1:
                print "%s is not a 1:1 mapping: %s" % item
                sys.exit(1)
            k = key[0]
            v = val[0]
            if isinstance(v, list):
                for subitem in v:
                    if not isinstance(
                            subitem,
                            str) and not isinstance(
                            subitem,
                            unicode):
                        print "'%s' is not a valid string" % v
                        sys.exit(1)
                    func(k, subitem)
            elif isinstance(v, str) or isinstance(v, unicode):
                func(k, v)
            else:
                print "'%s' is not a valid string or list of strings" % v
                sys.exit(1)
        else:
            print "Invalid item in '%s': %s" % (fname, item)
            sys.exit(1)
