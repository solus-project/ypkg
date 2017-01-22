#!/bin/true
# -*- coding: utf-8 -*-
#
#  This file is part of ypkg2
#
#  Copyright 2015-2016 Ikey Doherty <ikey@solus-project.com>

#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

from . import console_ui, pkgconfig_dep, pkgconfig32_dep
from . import packager_name, packager_email

import os
import pisi.util
import pisi.metadata
import pisi.specfile
import pisi.package
from pisi.db.installdb import InstallDB
import stat
import subprocess
from collections import OrderedDict
import datetime
import calendar
import sys


FileTypes = OrderedDict([
    ("/usr/lib/pkgconfig", "data"),
    ("/usr/lib64/pkgconfig", "data"),
    ("/usr/lib32/pkgconfig", "data"),
    ("/usr/libexec", "executable"),
    ("/usr/lib", "library"),
    ("/usr/share/info", "info"),
    ("/usr/share/man", "man"),
    ("/usr/share/doc", "doc"),
    ("/usr/share/help", "doc"),
    ("/usr/share/gtk-doc", "doc"),
    ("/usr/share/locale", "localedata"),
    ("/usr/include", "header"),
    ("/usr/bin", "executable"),
    ("/bin", "executable"),
    ("/usr/sbin", "executable"),
    ("/sbin", "executable"),
    ("/etc", "config"),
])

history_timestamp = None
history_date = None
fallback_timestamp = None

accum_packages = dict()


def unix_seconds_for_date(date):
    tp = datetime.datetime.timetuple(date)
    return calendar.timegm(tp)


def utc_date_for_date_only(date):
    d = datetime.datetime.strptime(date, "%Y-%m-%d")
    offset = datetime.datetime.utcnow() - datetime.datetime.now()
    lutc = d - offset
    history_timestamp = unix_seconds_for_date(lutc)
    return unix_seconds_for_date(lutc)


def initialize_timestamp(spec):
    """ To support reproducible builds, we need to ensure we utime them to
        some valid value. This is basically whatever the next update time
        would be in our spec.. """
    global history_date
    global history_timestamp
    global fallback_timestamp

    # If it was already set, just skip it.
    if history_timestamp is not None:
        dt = datetime.datetime.fromtimestamp(history_timestamp)
        history_date = dt.strftime("%Y-%m-%d")
        fallback_timestamp = history_timestamp
        return

    dt = datetime.datetime.utcnow()
    s = dt.strftime("%Y-%m-%d")
    fallback_timestamp = utc_date_for_date_only(s)

    if spec.history:
        up = spec.history.history[0]
        history_timestamp = utc_date_for_date_only(up.date)
    else:
        history_timestamp = fallback_timestamp

    history_date = s


def get_file_type(t):
    """ Return the fileType for a given file. Defaults to data """
    for prefix in FileTypes:
        if t.startswith(prefix):
            return FileTypes[prefix]
    return "data"


def readlink(path):
    return os.path.normpath(os.readlink(path))


def create_files_xml(context, package):
    """ Create an XML representation of our files """
    files = pisi.files.Files()
    global history_timestamp

    # TODO: Remove reliance on pisi.util functions completely.

    for path in sorted(package.emit_files()):
        if path[0] == '/':
            path = path[1:]

        full_path = os.path.join(context.get_install_dir(), path)
        fpath, hash = pisi.util.calculate_hash(full_path)

        if os.path.islink(fpath):
            fsize = long(len(readlink(full_path)))
            st = os.lstat(fpath)
        else:
            fsize = long(os.path.getsize(full_path))
            st = os.stat(fpath)

        permanent = package.is_permanent("/" + path)
        if not permanent:
            permanent = None
        else:
            permanent = "true"
        ftype = get_file_type("/" + path)

        if (stat.S_IMODE(st.st_mode) & stat.S_ISUID):
            # Preserve compatibility with older eopkg implementation
            console_ui.emit_warning("Package", "{} has suid bit set".
                                    format(full_path))

        path = path.decode("latin1").encode('utf-8')
        file_info = pisi.files.FileInfo(path=path, type=ftype,
                                        permanent=permanent, size=fsize,
                                        hash=hash, uid=str(st.st_uid),
                                        gid=str(st.st_gid),
                                        mode=oct(stat.S_IMODE(st.st_mode)))
        files.append(file_info)

    fpath = os.path.join(context.get_packaging_dir(), "files.xml")
    files.write(fpath)
    os.utime(fpath, (history_timestamp, history_timestamp))
    return files


def create_packager(name, email):
    """ Factory: Create a packager """
    packager = pisi.specfile.Packager()
    packager.name = unicode(name)
    packager.email = str(email)
    return packager


def metadata_from_package(context, package, files):
    """ Base metadata cruft. Tedious   """
    global history_date
    global history_timestamp
    global fallback_timestamp
    global accum_packages

    meta = pisi.metadata.MetaData()
    spec = context.spec

    packager = create_packager(spec.packager_name, spec.packager_email)

    component = context.spec.get_component(package.name)
    summary = context.spec.get_summary(package.name)
    description = context.spec.get_description(package.name)

    meta.source.name = spec.pkg_name
    meta.source.homepage = spec.pkg_homepage
    meta.source.packager = packager

    meta.package.source = meta.source
    meta.package.source.name = spec.pkg_name
    meta.package.name = context.spec.get_package_name(package.name)

    update = None
    if context.spec.history:
        topup = context.spec.history.history[0]
        l_release = int(topup.release)
        l_version = topup.version
        version = context.spec.pkg_version
        release = context.spec.pkg_release
        if l_release != release or l_version != version:
            console_ui.emit_info("History", "Constructing new history entry")
            history_timestamp = fallback_timestamp
        else:
            # Last updater is listed as maintainer in eopkg blame
            update = topup
            packager.name = topup.name
            packager.email = topup.email
            meta.package.history = context.spec.history.history

    if not update:
        update = pisi.specfile.Update()
        update.comment = "Packaging update"
        update.name = packager.name
        update.email = packager.email

        update.date = history_date
        update.release = str(spec.pkg_release)
        update.version = spec.pkg_version
        meta.package.history.append(update)

    meta.package.source.packager = packager

    meta.package.summary['en'] = summary
    meta.package.description['en'] = description

    if component is not None:
        meta.package.partOf = str(component)
    for license in spec.pkg_license:
        meta.package.license.append(str(license))

    # TODO: Add everything else...
    meta.source.version = spec.pkg_version
    meta.source.release = spec.pkg_release
    meta.package.version = spec.pkg_version
    meta.package.release = spec.pkg_release

    accum_packages[package.name] = meta
    return meta


def construct_package_name(context, package):
    """ .eopkg path """
    extension = "eopkg"
    name = context.spec.get_package_name(package.name)
    config = context.pconfig

    did = config.values.general.distribution_release
    parts = [
              name,
              context.spec.pkg_version,
              str(context.spec.pkg_release),
              did,
              config.values.general.architecture]
    return "{}.{}".format("-".join(parts), extension)

global idb

idb = None


def handle_dependencies(context, gene, metadata, package, files):
    """ Insert providers and dependencies into the spec """
    global idb

    # Insert the simple guys first, replaces/conflicts, as these don't map
    # to internal names at all and are completely from the user
    if package.name in context.spec.replaces:
        for item in sorted(set(context.spec.replaces[package.name])):
            repl = pisi.replace.Replace()
            repl.package = str(item)
            metadata.package.replaces.append(repl)
    # conflicts
    if package.name in context.spec.conflicts:
        for item in sorted(set(context.spec.conflicts[package.name])):
            conf = pisi.conflict.Conflict()
            conf.package = str(item)
            metadata.package.conflicts.append(conf)

    if len(package.provided_symbols) > 0:
        for sym in package.provided_symbols:
            spc = None
            name = None
            g = pkgconfig32_dep.match(sym)
            if g:
                spc = pisi.specfile.PkgConfig32Provide()
                spc.om = g.group(1)
                metadata.package.providesPkgConfig32.append(spc)
            g = pkgconfig_dep.match(sym)
            if g:
                spc = pisi.specfile.PkgConfigProvide()
                spc.om = g.group(1)
                metadata.package.providesPkgConfig.append(spc)

    all_names = set()
    for i in gene.packages:
        all_names.add(context.spec.get_package_name(i))

    dependencies = set(package.depend_packages)

    # Ensure some sane defaults are in place
    if package.name == "32bit" and "main" in gene.packages:
        dependencies.add(context.spec.get_package_name("main"))
    elif package.name == "32bit-devel":
        if "32bit" in gene.packages:
            dependencies.add(context.spec.get_package_name("32bit"))
        if "devel" in gene.packages:
            dependencies.add(context.spec.get_package_name("devel"))
    elif package.name == "devel":
        if "main" in gene.packages:
            dependencies.add(context.spec.get_package_name("main"))
    elif package.name == "dbginfo":
        if "main" in gene.packages:
            dependencies.add(context.spec.get_package_name("main"))
    elif package.name == "32bit-dbginfo":
        if "32bit" in gene.packages:
            dependencies.add(context.spec.get_package_name("32bit"))

    for dependency in dependencies:
        release = context.spec.pkg_release

        newDep = pisi.dependency.Dependency()

        local_fullname = context.spec.get_package_name(package.name)

        # Don't self depend.
        if dependency == local_fullname:
            continue
        if dependency not in all_names:
            # External dependency
            if not idb:
                idb = InstallDB()
            pkg = idb.get_package(dependency)
            newDep.package = dependency
            newDep.releaseFrom = str(pkg.release)
        else:
            newDep.package = dependency
            newDep.release = str(release)

        metadata.package.packageDependencies.append(newDep)

    if package.name not in context.spec.rundeps:
        return
    # Handle pattern/ypkg spec rundep
    for depname in context.spec.rundeps[package.name]:
        if depname in dependencies:
            continue
        dep = pisi.dependency.Dependency()
        if depname in all_names:
            dep.releaseFrom = str(context.spec.pkg_release)
        dep.package = str(depname)
        metadata.package.packageDependencies.append(dep)


def create_meta_xml(context, gene, package, files):
    """ Create the main metadata.xml file """
    global history_timestamp

    meta = metadata_from_package(context, package, files)
    config = context.pconfig

    iSize = sum([x.size for x in files.list])
    meta.package.installedSize = iSize

    meta.package.buildHost = config.values.build.build_host

    meta.package.distribution = config.values.general.distribution
    meta.package.distributionRelease = \
        config.values.general.distribution_release
    meta.package.architecture = config.values.general.architecture
    meta.package.packageFormat = pisi.package.Package.default_format

    handle_dependencies(context, gene, meta, package, files)

    mpath = os.path.join(context.get_packaging_dir(), "metadata.xml")
    meta.write(mpath)
    os.utime(mpath, (history_timestamp, history_timestamp))

    return meta


def create_eopkg(context, gene, package, outputDir):
    """ Do the hard work and write the package out """
    global history_timestamp

    name = construct_package_name(context, package)
    fpath = os.path.join(outputDir, name)

    if os.path.abspath(os.path.dirname(fpath)) == os.path.abspath(os.getcwd()):
        console_ui.emit_info("Package", "Creating {} ...".format(name))
    else:
        console_ui.emit_info("Package", "Creating {} ...".format(fpath))

    # Grab Files XML
    pdir = context.get_packaging_dir()
    files = create_files_xml(context, package)
    # Grab Meta XML
    meta = create_meta_xml(context, gene, package, files)
    # Start creating a package.

    try:
        pkg = pisi.package.Package(fpath, "w",
                                   format=pisi.package.Package.default_format,
                                   tmp_dir=pdir)
    except Exception as e:
        console_ui.emit_error("Build", "Failed to emit package: {}".
                              format(e))
        sys.exit(1)

    if history_timestamp:
        pkg.history_timestamp = history_timestamp

    pkg.add_metadata_xml(os.path.join(pdir, "metadata.xml"))
    pkg.add_files_xml(os.path.join(pdir, "files.xml"))

    for finfo in pkg.files.list:
        # old eopkg trick to ensure the file names are all valid
        orgname = os.path.join(context.get_install_dir(), finfo.path)
        orgname = orgname.encode('utf-8').decode('utf-8').encode("latin1")

        if os.path.islink(orgname) and not os.path.isdir(orgname):
            t = history_timestamp
            cmd = "touch -d \"@{}\" -h \"{}\"".format(t, orgname)
            try:
                subprocess.check_call(cmd, shell=True)
            except Exception as e:
                console_ui.emit_warning("utime", "Failed to modify utime")
                print("Reproducible builds will be affected: {}".format(e))
        else:
            try:
                os.utime(orgname, (history_timestamp, history_timestamp))
            except Exception as e:
                console_ui.emit_warning("utime", "Failed to modify utime")
                print("Reproducible builds will be affected: {}".format(e))

        pkg.add_to_install(orgname, finfo.path)

    pfile = os.path.join(pdir, "install.tar.xz")
    os.utime(pfile, (history_timestamp, history_timestamp))
    try:
        pkg.close()
    except Exception as e:
        console_ui.emit_error("Build", "Failed to emit package: {}".
                              format(e))
        sys.exit(1)


def write_spec(context, gene, outputDir):
    """ Write out a compatibility pspec_$ARCH.xml """
    global accum_packages

    packages = list()
    if "main" in gene.packages:
        packages.append("main")
        packages.extend(sorted([x for x in gene.packages if x != "main"]))
    else:
        packages = list(sorted(gene.packages.keys()))

    spec = pisi.specfile.SpecFile()

    legacy_sha1 = "79eb0752a961b8e0d15c77d298c97498fbc89c5a"
    legacy_url = "https://solus-project.com/sources/README.Solus"

    history = None
    pkg_main = accum_packages[packages[0]]
    spec.history = pkg_main.package.history
    spec.source = pisi.specfile.Source()
    spec.source.name = context.spec.pkg_name
    spec.source.summary['en'] = context.spec.get_summary("main")
    spec.source.description['en'] = context.spec.get_description("main")
    spec.source.homepage = context.spec.pkg_homepage
    spec.source.packager = pkg_main.source.packager
    spec.source.license = pkg_main.package.license
    spec.source.partOf = pkg_main.package.partOf
    spec.source.buildDependencies = list()

    # Avoid unnecessary diffs
    archive = pisi.specfile.Archive()
    archive.sha1sum = legacy_sha1
    archive.uri = legacy_url
    archive.type = "binary"
    spec.source.archive.append(archive)

    all_names = set()
    for i in gene.packages:
        all_names.add(context.spec.get_package_name(i))

    for pkg in packages:
        package = accum_packages[pkg]

        if pkg == "dbginfo" or pkg == "32bit-dbginfo":
            continue

        specPkg = pisi.specfile.Package()
        copies = ["name", "summary", "description", "partOf",
                  "replaces", "conflicts"]
        for item in copies:
            if not hasattr(package.package, item):
                continue
            setattr(specPkg, item, getattr(package.package, item))

        # Now the fun bit.
        for f in sorted(gene.packages[pkg].emit_files_by_pattern()):
            fc = pisi.specfile.Path()
            fc.path = f
            fc.fileType = get_file_type(f)
            specPkg.files.append(fc)
        for dep in package.package.packageDependencies:
            if dep.package not in all_names:
                continue
            specPkg.packageDependencies.append(dep)

        spec.packages.append(specPkg)

    opath = os.path.join(outputDir, "pspec_{}.xml".format(context.build.arch))
    try:
        spec.write(opath)
    except Exception as e:
        console_ui.emit_error("Build", "Cannot write pspec file")
        print(e)
        sys.exit(1)
