#!/usr/bin/env python
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
import stat
from collections import OrderedDict

FileTypes = OrderedDict([
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


def get_file_type(t):
    """ Return the fileType for a given file. Defaults to data """
    for prefix in FileTypes:
        if t.startswith(prefix):
            return FileTypes[prefix]
    return "data"


def readlink(path):
    return os.path.normpath(os.readlink(path))


def create_files_xml(context, package):
    console_ui.emit_info("Package", "Emitting files.xml for {}".
                         format(package.name))

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

        path = path.decode("latin1").encode('utf-8')
        file_info = pisi.files.FileInfo(path=path, type=ftype,
                                        permanent=permanent, size=fsize,
                                        hash=hash, uid=str(st.st_uid),
                                        gid=str(st.st_gid),
                                        mode=oct(stat.S_IMODE(st.st_mode)))
        files.append(file_info)

    # Temporary!
    files.write("files.xml")
    return True
