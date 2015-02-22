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
import pisi.metadata
import pisi.specfile
import os
import re
import fnmatch
import yaml
import time
import datetime
import sanity

conf = pisi.config.Config()

def packageit(ymlFile, installDIR, outputXML):
    wdir = installDIR

    d = None
    with open(ymlFile, "r") as pkg:
        d = yaml.load(pkg)

    spec = pisi.specfile.SpecFile()
    meta = pisi.metadata.MetaData()
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
    def m(s):
        return re.compile(s)
    #patterns["/etc/"] = "-config"
    patterns["/usr/share/locale"] = name
    patterns["/usr/lib64/lib*.so"] = "-devel"
    patterns["/usr/lib64/lib*.so.*"] = name
    patterns["/usr/share/pkgconfig"] = "-devel"
    patterns["/usr/lib64/pkgconfig"] = "-devel"
    patterns["/usr/include"] = "-devel"
    patterns["/usr/share/help"] = name
    patterns["/usr/share/gtk-doc"] = "-docs"
    patterns["/usr/share/man/man2"] = "-devel"
    patterns["/usr/share/man/man3"] = "-devel"
    # these just exist to speed things up tbqh.
    patterns["/usr/share/icons"] = name
    patterns["/usr/share/man"] = name
    patterns["/usr/lib64/%s" % name] = name
    patterns["/usr/lib32/%s" % name] = name
    patterns["/usr/share/%s" % name] = name
    patterns["/usr/bin"] = name
    patterns["/usr/sbin"] = name
    # These things are because evil.
    rtable = dict()
    libr = re.compile("^/usr/(lib64|lib32)/[^/]*.\.so\..*") # main
    libdr = re.compile("^/usr/(lib64|lib32)/[^/]*.\.so$")
    rtable["/usr/lib64/lib*.so.*"] = libr # main
    rtable["/usr/lib64/lib*.so"] = libdr

    pkgFiles = dict()
    for root,dirs,files in os.walk(wdir):
        #print dirs
        for file in files:
            fpath = os.path.join(root, file)
            fpath = fpath.split(wdir)[1]
            hit = False
            # Ideally we need a shitlist of regex's to ignroe.
            if "lib" in fpath and fpath.endswith(".la"):
                continue
            for p in patterns:
                if p in rtable:
                    b = rtable[p].match(fpath)
                else:
                    b = fnmatch.fnmatch(fpath, p)
                    if not b:
                        b = fpath.startswith(p)
                if b:
                    comp = patterns[p]
                    if comp not in pkgFiles:
                        pkgFiles[comp] = list()
                    if p not in pkgFiles[comp]:
                        # Determine type, etc...
                        pkgFiles[comp].append(p)
                    hit = True
                    break
            if not hit:
                if name not in pkgFiles:
                    pkgFiles[name] = list()
                if fpath not in pkgFiles[name]:
                    pkgFiles[name].append(fpath)

    summaries = dict()
    summaries["-devel"] = "Development files for %s" % name
    summaries["-locale"] = "Localisation files for %s" % name
    summaries["-docs"] = "Documentation for %s" % name
    summaries["-help"] = "Help files for %s" % name

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
            package.packageDependencies.append(dep)
        package.description = source.description
        if fq != name:
            package.summary['en'] = summaries[pkg]
        else:
            package.summary['en'] = d['summary']
        spec.packages.append(package)

    spec.write(outputXML)
