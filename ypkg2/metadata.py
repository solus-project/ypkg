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

        # TODO: Fix this
        ftype = "data"

        path = path.decode("latin1").encode('utf-8')
        file_info = pisi.files.FileInfo(path=path, type=ftype,
                                        permanent=permanent, size=fsize,
                                        hash=hash, uid=str(st.st_uid),
                                        gid=str(st.st_gid),
                                        mode=oct(stat.S_IMODE(st.st_mode)))
        files.append(file_info)

    # Temporary!
    files.write("files.xml")
