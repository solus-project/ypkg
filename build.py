#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  build.py
#  
#  Copyright 2015 Ikey Doherty <ikey@solus-project.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
import yaml
from configobj import ConfigObj
import tempfile
import os.path
import sys
import subprocess
import hashlib

import sanity

import pisi.config
conf = pisi.config.Config()

LeRoot = os.geteuid() == 0

BuildPrefix =  "/var/ypkg-root" if LeRoot else "%s/YPKG" % os.path.expanduser("~")
global BallDir
BallDir = conf.values.dirs.archives_dir if LeRoot else os.path.abspath("%s/sources" % BuildPrefix)

global BuildDir
BuildDir = os.path.abspath("%s/build" % BuildPrefix)

global InstallDir
InstallDir = os.path.abspath("%s/install" % BuildPrefix)

global host
host = conf.values.build.host

global arch
arch = conf.values.general.architecture

global ccache
ccache = conf.values.build.buildhelper is not None and "ccache" in conf.values.build.buildhelper

global fakeroot
fakeroot = False

def which(p):
    for i in os.environ['PATH'].split(":"):
        p2 = os.path.join(i,p)
        if os.path.exists(p2):
            return True
    return False

global Clang
Clang = False

global emul32
emul32 = False

global pkgfile

def get_path():
    path = "/usr/bin:/bin"
    if ccache and sanity.can_ccache:
        cpath = ""
        if os.path.exists("/usr/lib/ccache/bin"):
            cpath = "/usr/lib/ccache/bin"
        elif os.path.exists("/usr/lib64/ccache/bin"):
            cpath = "/usr/lib64/ccache/bin"
        if cpath != "":
            print "Enabling ccache"
            path = "%s:%s" % (cpath, path)
    return path

def escape(inp, wdir, name):
    global host
    global arch
    global BallDir
    cxxflags = conf.values.build.cxxflags
    cflags = conf.values.build.cflags
    ldflags = conf.values.build.ldflags

    x86 = "x86_64" in arch

    libdir = "lib64" if x86 else "lib"
    if emul32:
        libdir = "lib32"

    libsuffix = "64" if x86 and not emul32 else ""

    macros = dict()
    macros["%libdir%"] = "/usr/%s" % libdir
    macros["%configure"] = "./configure $CONFOPTS"
    macros["%make_install"] = "%make install DESTDIR=%installroot%"
    macros["%installroot%"] = InstallDir
    macros["%workdir%"] = wdir
    macros["%cmake"] = "cmake -DCMAKE_INSTALL_PREFIX=/usr \
                      -DCMAKE_C_FLAGS=\"%s\" \
                      -DCMAKE_CXX_FLAGS=\"%s\" \
                      -DCMAKE_LD_FLAGS=\"%s\" \
                      -DCMAKE_LIB_SUFFIX=\"%s\" \
                      -DCMAKE_BUILD_TYPE=RelWithDebInfo" % (cflags, cxxflags, ldflags, libsuffix)

    # common issues...
    # -mtune=generic -march=x86-64
    # only x86_64 for emul32 builds right now
    if emul32 and x86:
        if "-march=%s" % arch in cflags:
            cflags = cflags.replace("-march=%s" % arch, "-march=i686")
        if "-march=%s" % arch in cxxflags:
            cxxflags = cxxflags.replace("-march=%s" % arch, "-march=i686")
        host = "i686-pc-linux-gnu"

    prefix = "/usr" if not emul32 else "/emul32"

    macros["$CONFOPTS"] = "--prefix=%s \
                           --build=%s \
                           --libdir=/usr/%s \
                           --mandir=/usr/share/man \
                           --infodir=/usr/share/man \
                           --datadir=/usr/share/ \
                           --sysconfdir=/etc \
                           --localstatedir=/var \
                           --libexecdir=/usr/%s/%s" % (prefix, host, libdir, libdir, name)
    macros["%CFLAGS%"] = cflags
    macros["%CXXFLAGS%"] = cxxflags
    macros["%LDFLAGS%"] = conf.values.build.ldflags
    macros["%CC%"] = "%s-gcc" % host
    macros["%CXX%"] = "%s-g++" % host
    macros["%JOBS%"] = conf.values.build.jobs
    macros["%make"] = "make %JOBS%"
    macros["%patch"] = "patch -t --remove-empty-files --no-backup-if-mismatch"
    macros["%package%"] = sanity.name
    macros["%version%"] = sanity.version
    macros["%release%"] = sanity.release
    macros["%sources%"] = BallDir

    # We like clang
    if Clang:
        macros["%CC%"] = "clang"
        macros["%CXX%"] = "clang++"

    if emul32:
        if Clang:
            macros["%CC%"] += " -m32"
            macros["%CXX%"] += " -m32"
        else:
            macros["%CC%"] = "gcc -m32"
            macros["%CXX%"] = "g++ -m32"
    # presetup, required. Cool how we disobey our own /bin rule right?
    header = """
#!/bin/bash
set -e
set -x
export TERM=dumb
cd %%workdir%%;
export CFLAGS="%%CFLAGS%%"
export CXXFLAGS="%%CXXFLAGS%%"
export LDFLAGS="%%LDFLAGS%%"
export CC="%%CC%%"
export CXX="%%CXX%%"
export PATH="%s"
export srcdir="%%workdir%%"
export installdir="%%installroot%%"
export package="%%package%%"
export release="%%release%%"
export version="%%version%%"
export sources="%%sources%%"
export LD_AS_NEEDED=1
""" % get_path()
    if emul32:
        header += "\nexport EMUL32BUILD=1\n"

    if LeRoot:
        header += """
export CCACHE_DIR=/root/.ccache
"""

    pkgfiles = get_pkgfiles_dir()
    if pkgfiles is not None:
        header += """
export pkgfiles="%s"
""" % pkgfiles

    header += inp
    inp = header

    if emul32:
        inp += """
if [ -e "%installroot%/emul32" ]; then
        rm -rf "%installroot%/emul32"
fi"""

    # General cleanup crap
    inp += """
if [ -f "%installroot%/usr/share/man/dir" ]; then
    rm -v "%installroot%/usr/share/man/dir"
fi
find "%installroot%/%libdir%" -type f -name *.la|xargs rm -rf
"""

    while (True):
        co = False
        for macro in macros:
            if macro in inp:
                inp = inp.replace(macro, macros[macro])
        # now..
        for macro in macros:
            if macro in inp:
                co = True
                break
        if not co:
            break
    return inp


def cleanup():
    if os.path.exists(BuildDir) and os.path.isdir(BuildDir):
        print "Removing %s" % BuildDir
        os.system("rm -rf \"%s\"" % BuildDir)
    if os.path.exists(InstallDir) and os.path.isdir(InstallDir):
        print "Removing %s" % InstallDir
        os.system("rm -rf \"%s\"" % InstallDir)

def fetch_source(sources):
    tars = None
    if not os.path.exists(BallDir):
        os.makedirs(BallDir)
    for source_item in sources:
        source = source_item.uri
        endName = os.path.basename(source)
        fname = os.path.join(BallDir, endName)
        if not os.path.exists(fname):
            try:
                p = subprocess.check_call("wget -O \"%s\" \"%s\"" % (fname, source), shell=True)
            except:
                print "Abnormal exit from download"
                sys.exit(1)
        else:
            print "Skipping download of %s" % endName
        hash = None
        with open(fname, "r") as inp:
            h = hashlib.sha256()
            h.update(inp.read())
            hash = h.hexdigest()
        if hash != source_item.hash:
            print "Incorrect hash for %s: %s" % (endName, hash)
            sys.exit(1)
        if not tars:
            tars = list()
            tars.append(source)
    return tars

def extract(src_list):
    if not os.path.exists(BuildDir):
        os.makedirs(BuildDir)

    for x in src_list:
        target = os.path.join(BallDir, os.path.basename(x))
        ext = "unzip" if target.endswith(".zip") else "tar xf"
        diropt = "-d" if target.endswith(".zip") else "-C"
        cmd = "%s \"%s\" %s \"%s\"" % (ext, target, diropt, BuildDir)
        r = subprocess.check_call(cmd, shell=True)

def get_work_dir():
    kids = os.listdir(BuildDir)
    if len(kids) > 1:
        return BuildDir
    else:
        return os.path.join(BuildDir, kids[0] if len(kids) > 0 else BuildDir)

def get_pkgfiles_dir():
    dirn = os.path.dirname(pkgfile)
    fpath = os.path.abspath(dirn)
    fdir = os.path.join(fpath, "files")
    if os.path.exists(fdir):
        return fdir
    return None

def build(fpath):
    global pkgfile

    pkgfile = fpath

    with open(fpath, "r") as pkg:
        d = yaml.load(pkg)
        print "building %s" % d['name']

        wdir = get_work_dir()
        if "clang" in d:
            cl = bool(d['clang'])
            if cl:
                print "Enabling clang"
            global Clang
            Clang = cl

        name = d['name']

        if 'setup' in d:
            setup = d['setup']
            contents = escape(setup, wdir, name)

            with tempfile.NamedTemporaryFile(prefix="eopkg-setup") as script:
                script.writelines(contents)
                script.flush()
                # execute it :/
                print "Running setup..."
                if fakeroot:
                    cmd = ["fakeroot", "/bin/sh", script.name]
                else:
                    cmd = ["/bin/sh", script.name]
                r = subprocess.check_call(cmd)

        if 'build' in d:
            contents = escape(d['build'], wdir, name)
            with tempfile.NamedTemporaryFile(prefix="eopkg-build") as script:
                script.writelines(contents)
                script.flush()
                # execute it :/
                print "Running build..."
                if fakeroot:
                    cmd = ["fakeroot", "/bin/sh", script.name]
                else:
                    cmd = ["/bin/sh", script.name]
                r = subprocess.check_call(cmd)


        if 'install' in d:
            contents = escape(d['install'], wdir, name)
            with tempfile.NamedTemporaryFile(prefix="eopkg-install") as script:
                script.writelines(contents)
                script.flush()
                # execute it :/
                print "Running install..."
                if fakeroot:
                    cmd = ["fakeroot", "/bin/sh", script.name]
                else:
                    cmd = ["/bin/sh", script.name]
                r = subprocess.check_call(cmd)
