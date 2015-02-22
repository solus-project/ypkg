#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  sanity.py
#  
#  Copyright 2015 Ikey Doherty <ikey@evolve-os.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
import yaml
import os
import sys
import re
import pisi.db
from configobj import ConfigObj

global name

global pkger_name
global pkger_email

def assertGetString(y, n):
    ''' Ensure string value exists '''
    if n not in y:
        print "Required string '%s' missing" % n
        sys.exit(1)
    r = y[n]
    if not isinstance(r, str):
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
    r = y[n]
    if not isinstance(r, str):
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
    if isinstance(r, str):
        ret.append(r)
    elif isinstance(r, list):
        for i in r:
            if not isinstance(i, str):
                print "[%s] Item '%s' is not a string" % (n,i)
                sys.exit(1)
            ret.append(i)
    else:
        print "'%s' is neither a string or list of strings" % n
    return ret



_idb = pisi.db.installdb.InstallDB()
_pdb = pisi.db.packagedb.PackageDB()
def get_build_deps(y):
    ''' Get the eopkg version of the .pc files, and dependencies '''
    if "builddeps" not in y:
        return None

    rgx = "^pkgconfig\((.*)\)$"
    r = re.compile(rgx)
    depList = list()
    pcs = list()
    l = assertStringList(y, "builddeps")
    for dep in l:
        m = r.search(dep)
        if m:
            pcs.append(m.group(1))
        else:
            depList.append(dep)
    for pc in pcs:
        ret = _pdb.get_package_by_pkgconfig(pc)
        if not ret:
            print "Warning: build dep does not exist in repo: %s" % pc
        
            ret = _idb.get_package_by_pkgconfig(pc)
            if ret is None:
                print "Requested build dep does not exist! %s" % pc
                sys.exit(1)
        if ret.name in depList:
            print "Info: %s is already in dependency list.." % pc
        else:
            depList.append(ret.name)
    return depList

global _sources
_sources = None

def get_sources():
    return _sources

class TarSource:
    uri = None
    hash = None

    def __str__(self):
        return "%s (%s)" % (self.uri, self.hash)

def sane(fpath):
    ''' Determine if the conf is actually, yknow, sane. '''
    if not os.path.exists(fpath):
        print "%s does not exist, bailing"
        return False
    y = None
    f = None
    try:
        f = open(fpath, "r")
        y = yaml.load(f)
    except Exception, e:
        print "Unable to load %s: %s" % (fpath, e)
        return False

    # Required !
    assertGetString(y, "name")
    v = assertGetString(y, "version")
    try:
        vr = pisi.version.make_version(v)
    except Exception, e:
        print vr
        sys.exit(1)

    assertGetString(y, "description")
    assertGetString(y, "summary")
    assertGetInteger(y, "release")


    global name
    name = y['name']

    if not "source" in y:
        print "Required list '%s' is missing" % "source"
        sys.exit(1)

    # Determine packager...
    confPath = "%s/.evolveos/packager" % os.path.expanduser("~")
    if not os.path.exists:
        print "Ensure %s exists!"
        print "[Packager]"
        print "Name=Your Name Here"
        print "Email=yourAwesome@email.address"
        return 1

    confObj = ConfigObj(confPath)
    global pkger_name
    pkger_name = confObj["Packager"]["Name"]
    global pkger_email
    pkger_email = confObj["Packager"]["Email"]

    ''' Determine sources... Kinda need these '''
    srcs = y["source"]
    sources = list()
    if not isinstance(srcs, list):
        print "'source' is not a valid list"
        sys.exit(1)
    for item in srcs:
        if not isinstance(item, dict):
            print "Item is not a correct URI:HASH mapping: %s" % item
            sys.exit(1)
        key = item.keys()
        val = item.values()
        if len(key) != 1 or len(val) != 1:
            print "%s is not a 1:1 mapping: %s" % item
            sys.exit(1)
        k = key[0]
        v = val[0]
        if not isinstance(k, str):
            print "'%s' is not a valid string" % k
            sys.exit(1)
        if not isinstance(v, str):
            print "'%s' is not a valid string" % v
            sys.exit(1)
        src = TarSource()
        src.uri = k
        src.hash = v
        sources.append(src)
    global _sources
    _sources = sources

    # Fuzzy.
    assertIsString(y, "setup")
    assertIsString(y, "build")
    assertIsString(y, "install")

    # Saywat?
    if "setup" not in y and "build" not in y and "install" not in y:
        print "%s specifies no build instructions" % fpath
        sys.exit(1)

    # Obv.
    if "builddeps" in y:
        assertStringList(y, "builddeps")
        get_build_deps(y)

    f.close()

    return True
