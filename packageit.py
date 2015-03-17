#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  packageit.py
#  
#  Copyright 2015 Ikey Doherty <ikey@evolve-os.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
from pisi.package import Package
import pisi.specfile
import os
import re
import fnmatch
import yaml
import time
import datetime
import sanity

conf = pisi.config.Config()

component = None

def packageit(ymlFile, installDIR, outputXML):
    wdir = installDIR

    d = None
    with open(ymlFile, "r") as pkg:
        d = yaml.load(pkg)

    canSplitLibs = True
    if "libsplit" in d:
        canSplitLibs = bool(d['libsplit'])

    spec = pisi.specfile.SpecFile()
    source = pisi.specfile.Source()
    source.name = d['name']
    name = source.name
    source.summary['en'] = str(d['summary'])
    source.description['en'] = str(d['description'])
    if "homepage" in d:
        source.homepage = d['homepage']

    lc = d['license']
    licenses = list()
    if isinstance(lc, list):
        licenses = lc
    else:
        licenses = list()
        licenses.append(lc)
    for lic in licenses:
        source.license.append(lic)

    # LIES. #
    arch = pisi.specfile.Archive()
    source.archive.append(arch)
    arch.sha1sum = "083029a13c0c475bf42a4232c68a9caa6dbc763e"
    arch.uri = "https://evolve-os.com/sources/README"
    arch.type = "binary"

    # Seems legit.
    packager = pisi.specfile.Packager()
    packager.name = unicode(sanity.pkger_name)
    packager.email = sanity.pkger_email
    source.packager = packager

    spec.packages = list()

    spec.groups = None
    spec.source = source

    history = list()
    upd = pisi.specfile.Update()
    upd.release = str(d['release'])
    upd.version = str(d['version'])

    dt = datetime.datetime.now()
    #s = dt.strftime("%M-%D-%Y") # Why? Why couldn't it be this?
    s = dt.strftime("%Y-%m-%d")
    upd.date = s
    upd.comment = "Packaging update"
    upd.name = packager.name
    upd.email = packager.email
    history.append(upd)
    spec.history = history
    source.history = history


    patterns = dict()
    patterns["/usr/share/locale"] = name
    patterns["/usr/lib64/lib*.so"] = "-devel" if canSplitLibs else name
    patterns["/usr/lib/lib*.so"] = "-devel" if canSplitLibs else name
    patterns["/usr/lib64/lib*.so.*"] = name
    patterns["/usr/lib/lib*.so.*"] = name
    patterns["/usr/lib64/lib*.a"] = "-devel"
    patterns["/usr/lib/lib*.a"] = "-devel"
    patterns["/usr/lib32/lib*.a"] = "-32bit"
    # Consider splitting -devel .. just not that bothered tbh
    patterns["/usr/lib32/lib*.so"] = "-32bit"
    patterns["/usr/lib32/lib*.so.*"] = "-32bit"

    patterns["/usr/share/pkgconfig"] = "-devel"
    patterns["/usr/lib64/pkgconfig"] = "-devel"
    patterns["/usr/lib/pkgconfig"] = "-devel"
    patterns["/usr/include"] = "-devel"
    patterns["/usr/share/help"] = name
    patterns["/usr/share/gtk-doc"] = "-docs"
    patterns["/usr/share/man/man2"] = "-devel"
    patterns["/usr/share/man/man3"] = "-devel"
    patterns["/usr/share/vala*"] = "-devel"
    patterns["/usr/share/cmake*"] = "-devel"

    # these just exist to speed things up tbqh.
    patterns["/usr/share/icons"] = name
    patterns["/usr/share/pixmaps"] = name
    patterns["/usr/share/man"] = name
    patterns["/usr/bin"] = name
    patterns["/usr/sbin"] = name

    # These things are because evil.
    rtable = dict()

    libr64 = re.compile("^/usr/lib64/lib[^/]*.\.so\..*") # main
    libdr64 = re.compile("^/usr/lib64/lib[^/]*.\.so$")
    libar64 = re.compile("^/usr/lib64/lib[^/]*.\.a$")
    rtable["/usr/lib64/lib*.so.*"] = libr64 # main
    rtable["/usr/lib64/lib*.so"] = libdr64
    rtable["/usr/lib64/lib*.a"] = libar64

    libr = re.compile("^/usr/lib/lib[^/]*.\.so\..*") # main
    libdr = re.compile("^/usr/lib/lib[^/]*.\.so$")
    libar = re.compile("^/usr/lib/lib[^/]*.\.a$")
    rtable["/usr/lib/lib*.so.*"] = libr # main
    rtable["/usr/lib/lib*.so"] = libdr
    rtable["/usr/lib/lib*.a"] = libar

    libr32 = re.compile("^/usr/lib32/lib[^/]*.\.so\..*") # main
    libdr32 = re.compile("^/usr/lib32/lib[^/]*.\.so$")
    libar32 = re.compile("^/usr/lib32/lib[^/]*.\.a$")
    rtable["/usr/lib32/lib*.so.*"] = libr32
    rtable["/usr/lib32/lib*.so"] = libdr32
    rtable["/usr/lib32/lib*.a"] = libar32

    def hasMatch(path):
        for p in patterns:
            if p in rtable:
                b = rtable[p].match(path)
            else:
                b = fnmatch.fnmatch(path, p)
                if not b:
                    b = path.startswith(p)
            if b:
                return (p,patterns[p])
        return (None,None)

    # I am not proud of the following code.
    pkgFiles = dict()
    for root,dirs,files in os.walk(wdir):
        def scanFi(files):
            for file in files:
                fpath = os.path.join(root, file)
                fpath = fpath.split(wdir)[1]
                hit = False
                # Ideally we need a shitlist of regex's to ignore.
                if "lib" in fpath and fpath.endswith(".la"):
                    continue
                p,comp = hasMatch(fpath)
                if comp:
                    if comp not in pkgFiles:
                        pkgFiles[comp] = list()
                    if p not in pkgFiles[comp]:
                        pkgFiles[comp].append(p)
                else:
                    # Fallback.. nasty
                    tmpname = name
                    if fpath.startswith("/usr/lib32"):
                        tmpname = "-32bit"
                    collapsed = False
                    if len(files) > 1:
                        newname = os.path.dirname(fpath)
                        p,comp = hasMatch(newname)
                        if not p:
                            # Check nobody conflicts.
                            hit = False
                            for pkg in pkgFiles:
                                if pkg == name:
                                    continue
                                if newname in pkgFiles[pkg]:
                                    hit = True
                                    # Already collapsed/taken
                                    break
                                else:
                                    for fi in pkgFiles[pkg]:
                                        if fi.startswith(newname):
                                            # Recursive include
                                            hit = True
                                            break
                            if not hit:
                                # Actually collapse it.
                                if name not in pkgFiles:
                                    pkgFiles[name] = list()
                                if newname not in pkgFiles[name]:
                                    pkgFiles[name].append(newname)
                                collapsed = True

                    if not collapsed:
                        if tmpname not in pkgFiles:
                            pkgFiles[tmpname] = list()
                        if fpath not in pkgFiles[tmpname]:
                            pkgFiles[tmpname].append(fpath)

        if len(files) > 0:
            scanFi(files)
        # Catch empties
        for dir in dirs:
            fname = os.path.join(root, dir)
            if not os.listdir(fname):
                print "Warning: Empty directory: %s" % fname
                scanFi([fname])

    summaries = dict()
    summaries["-devel"] = "Development files for %s" % name
    summaries["-docs"] = "Documentation for %s" % name
    summaries["-32bit"] = "32-bit libraries for %s" % name

    for pkg in pkgFiles:
        type = "data"
        fq = pkg
        if fq.startswith("-"):
            fq = name + fq
        elif fq.endswith("-"):
            fq = fq + name
        print fq
        package = pisi.specfile.Package()
        package.name = fq
        for file in pkgFiles[pkg]:
            if file.startswith("/usr/lib/pkgconfig"):
                type = "data"
            elif file.startswith("/usr/lib64/pkgconfig"):
                type = "data"
            elif file.startswith("/usr/share/pkgconfig"):
                type = "data"
            elif file.startswith("/usr/lib"):
                type = "library"
            elif file.startswith("/usr/share/info"):
                type = "info"
            elif file.startswith("/usr/share/man"):
                type = "man"
            elif file.startswith("/usr/share/doc"):
                type = "doc"
            elif file.startswith("/usr/share/gtk-doc"):
                type = "doc"
            elif file.startswith("/usr/share/locale"):
                type = "localedata"
            elif file.startswith("/usr/include"):
                type = "header"
            elif file.startswith("/usr/bin"):
                type = "executable"
            elif file.startswith("/usr/sbin"):
                type = "executable"
            elif file.startswith("/etc"):
                type = "config"
            else:
                type = "data"
            path = pisi.specfile.Path()
            path.path = file
            path.fileType = type
            package.files.append(path)
        if fq != name:
            # needs runtime deps..
            package.packageDependencies = list()
            dep = pisi.dependency.Dependency()
            dep.package = name
            dep.release = "current"
            if fq.endswith("-devel"):
                if "devel" in d and bool(d['devel']) == True:
                    package.partOf = "system.devel"
                else:
                    package.partOf = "programming.devel"
            package.packageDependencies.append(dep)
        else:
            if component:
                package.partOf = component
        package.description = source.description
        if fq != name:
            package.summary['en'] = summaries[pkg]
        else:
            package.summary['en'] = d['summary']
        spec.packages.append(package)

    spec.write(outputXML)
