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

from . import console_ui

import os
import pisi.util
import pisi.metadata
import pisi.specfile
import pisi.package
import stat
import subprocess
from collections import OrderedDict

FileTypes = OrderedDict([
    ("/usr/lib/pkgconfig", "data"),
    ("/usr/lib64/pkgconfig", "data"),
    ("/usr/lib32/pkgconfig", "data"),
    ("/usr/lib", "library"),
    ("/usr/share/info", "info"),
    ("/usr/share/man", "man"),
    ("/usr/share/doc", "doc"),
    ("/usr/share/gtk-doc", "doc"),
    ("/usr/share/locale", "localedata"),
    ("/usr/include", "header"),
    ("/usr/bin", "executable"),
    ("/bin", "executable"),
    ("/usr/sbin", "executable"),
    ("/sbin", "executable"),
    ("/etc", "config"),
])

# 1980, Jan 1, for zip
TSTAMP_META = 315532800


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

        # We don't support this concept right now in ypkg.
        permanent = None
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
    os.utime(fpath, (TSTAMP_META, TSTAMP_META))
    return files


def create_packager(name, email):
    """ Factory: Create a packager """
    packager = pisi.specfile.Packager()
    packager.name = unicode(name)
    packager.email = str(email)
    return packager


def metadata_from_package(context, package, files):
    """ Base metadata cruft. Tedious   """
    meta = pisi.metadata.MetaData()
    spec = context.spec

    packager = create_packager("FIXME", "FIXME@NOTFIXED.FIXIT??")

    component = context.spec.get_component(package.name)
    summary = context.spec.get_summary(package.name)
    description = context.spec.get_description(package.name)

    meta.source.name = spec.pkg_name
    meta.source.homepage = spec.pkg_homepage
    meta.source.packager = packager

    meta.package.source = meta.source
    meta.package.source.name = spec.pkg_name
    meta.package.source.packager = packager
    meta.package.name = context.spec.get_package_name(package.name)

    update = pisi.specfile.Update()
    update.comment = "GRAB THE CORRECT COMMENT!!"
    update.name = packager.name
    update.email = packager.email
    update.date = "MAKE ME A DATE!!"
    update.release = str(spec.pkg_release)
    update.version = spec.pkg_version
    meta.package.history.append(update)

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


def create_meta_xml(context, package, files):
    """ Create the main metadata.xml file """
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

    mpath = os.path.join(context.get_packaging_dir(), "metadata.xml")
    meta.write(mpath)
    os.utime(mpath, (TSTAMP_META, TSTAMP_META))

    return meta


def create_eopkg(context, package):
    """ Do the hard work and write the package out """
    name = construct_package_name(context, package)

    console_ui.emit_info("Package", "Creating {} ...".format(name))

    # Grab Files XML
    pdir = context.get_packaging_dir()
    files = create_files_xml(context, package)
    # Grab Meta XML
    meta = create_meta_xml(context, package, files)
    # Start creating a package.
    pkg = pisi.package.Package(name, "w",
                               format=pisi.package.Package.default_format,
                               tmp_dir=pdir)

    pkg.add_metadata_xml(os.path.join(pdir, "metadata.xml"))
    pkg.add_files_xml(os.path.join(pdir, "files.xml"))

    for finfo in pkg.files.list:
        # old eopkg trick to ensure the file names are all valid
        orgname = os.path.join(context.get_install_dir(), finfo.path)
        orgname = orgname.encode('utf-8').decode('utf-8').encode("latin1")
        """
            This is all that's needed for reproducible builds right now.
            We need to grab the build time from somewhere sensible though

        if os.path.islink(orgname) and not os.path.isdir(orgname):
            cmd = "touch -d \"@{}\" -h \"{}\"".format(TSTAMP_META, orgname)
            try:
                subprocess.check_call(cmd, shell=True)
            except Exception as e:
                print e
                pass
        else:
            os.utime(orgname, (TSTAMP_META, TSTAMP_META))"""
        pkg.add_to_install(orgname, finfo.path)

    pfile = os.path.join(pdir, "install.tar.xz")
    os.utime(pfile, (TSTAMP_META, TSTAMP_META))
    pkg.close()
