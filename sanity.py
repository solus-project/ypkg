#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  sanity.py
#  
#  Copyright 2015 Ikey Doherty <ikey@solus-project.com>
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

global buildDeps
buildDeps = None

global emul32
emul32 = False

global autodep
autodep = True

global rundeps
rundeps = None

global pkg_replaces
pkg_replaces = None

global mutations
mutations = None

global pkg_patterns
pkg_patterns = None

global pkg_strip
pkg_strip = True

global pkg_extract
pkg_extract = True

global release
global version
global name

def init_mutations():
    global mutations

    if not mutations:
        mutations = dict()
        mutations["main"] = name
        mutations["devel"] = "%s-devel" % name
        mutations["docs"] = "%s-docs" % name
        mutations["32bit"] = "%s-32bit" % name
        mutations["utils"] = "%s-utils" % name

def add_runtime_dep(pkg, dep):
    ''' Explicitly add a package to the runtime dependencies '''
    global mutations
    global rundeps
    if not pkg or not dep:
        print "Required values missing for add_runtime_dep"
        sys.exit(1)

    init_mutations()

    pkgname = pkg
    if pkgname in mutations:
        pkgname = mutations[pkgname]

    if not rundeps:
        rundeps = dict()

    if pkgname not in rundeps:
        rundeps[pkgname] = list()

    if dep not in rundeps[pkgname]:
        rundeps[pkgname].append(dep)

def add_replaces(pkg, pkg2):
    ''' Explicitly replace one package with another '''
    global mutations
    global pkg_replaces

    if not pkg or not pkg2:
        print "Required values missing for add_replaces"
        sys.exit(1)

    init_mutations()

    pkgname = pkg
    if pkgname in mutations:
        pkgname = mutations[pkgname]

    if not pkg_replaces:
        pkg_replaces = dict()

    if pkgname not in pkg_replaces:
        pkg_replaces[pkgname] = list()

    if pkg2 not in pkg_replaces[pkgname]:
        pkg_replaces[pkgname].append(pkg2)

def add_pattern(pkg, pattern):
    ''' Explicitly add/override a default pattern '''
    global mutations
    global pkg_patterns

    if not pkg or not pattern:
        print "Required values missing for add_pattern"
        sys.exit(1)

    init_mutations()

    pkgname = pkg
    if pkgname not in mutations and pkgname != name:
        print "Unsupported pattern name: %s" % pkg
        sys.exit(1)

    if pkgname != name:
        pkgname = "-%s" % pkgname

    if not pkg_patterns:
        pkg_patterns = dict()

    if pattern in pkg_patterns:
        print "Duplicate pattern for %s: %s" % (pkg, pattern)
        sys.exit(1)
    pkg_patterns[pattern] = pkgname


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
        if isinstance(item, str):
            # main package
            func(name, item)
        elif isinstance(item, list):
            for subitem in item:
                if not isinstance(subitem, str):
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
                    if not isinstance(subitem, str):
                        print "'%s' is not a valid string" % v
                        sys.exit(1)
                    func(k, subitem)
            elif isinstance(v, str):
                func(k, v)
            else:
                print "'%s' is not a valid string or list of strings" % v
                sys.exit(1)
        else:
            print "Invalid item in '%s': %s" % (fname, item)
            sys.exit(1)

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
        print "%s is not a valid eopkg version" % v
        sys.exit(1)

    assertGetString(y, "description")
    assertGetString(y, "summary")
    assertGetInteger(y, "release")

    global version 
    global release
    release = str(assertGetInteger(y, "release"))
    version = str(v) 

    global name
    name = y['name']

    if "autodep" in y:
        global autodep
        autodep = bool(y['autodep'])
    if "strip" in y:
        global pkg_strip
        pkg_strip = bool(y['strip'])
    if "extract" in y:
        global pkg_extract
        pkg_extract = bool(y['extract'])

    if not "source" in y:
        print "Required list '%s' is missing" % "source"
        sys.exit(1)

    # Determine packager...
    confPathOld = "%s/.evolveos/packager" % os.path.expanduser("~")
    confPath = "%s/.solus/packager" % os.path.expanduser("~")
    if not os.path.exists(confPath):
        if os.path.exists(confPathOld):
            confPath = confPathOld
        else:
            print "Ensure %s exists!" % confPath
            print "[Packager]"
            print "Name=Your Name Here"
            print "Email=yourAwesome@email.address"
            sys.exit(1)

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

    if "rundeps" in y:
        rdeps = y["rundeps"]
        do_multimap(rdeps, "rundeps", add_runtime_dep)
    if "replaces" in y:
        rpl = y["replaces"]
        do_multimap(rpl, "replaces", add_replaces)
    if "patterns" in y:
        pat = y["patterns"]
        do_multimap(pat, "patterns", add_pattern)

    # Fuzzy.
    assertIsString(y, "setup")
    assertIsString(y, "build")
    assertIsString(y, "install")

    if "emul32" in y:
        global emul32
        emul32 = bool(y['emul32'])

    # Saywat?
    if "setup" not in y and "build" not in y and "install" not in y:
        print "%s specifies no build instructions" % fpath
        sys.exit(1)

    # Obv.
    if "builddeps" in y:
        assertStringList(y, "builddeps")
        b = get_build_deps(y)
        global buildDeps
        buildDeps = b

    f.close()

    return True
