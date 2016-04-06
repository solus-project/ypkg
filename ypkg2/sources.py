#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  This file is part of ypkg2
#
#  Copyright 2015-2016 Ikey Doherty <ikey@solus-project.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#

from . import console_ui

import os
import hashlib


class YpkgSource:

    def __init__(self):
        pass

    def fetch(self, context):
        """ Fetch this source from it's given location """
        return False

    def verify(self, context):
        """ Verify the locally obtained source """
        return False

    def extract(self, context):
        """ Attempt extraction of this source type, if needed """
        return False

    def remove(self, context):
        """ Attempt removal of this source type """
        return False

    def cached(self, context):
        """ Report on whether this source is cached """
        return False


class TarSource(YpkgSource):
    """ Represents a simple tarball source """

    uri = None
    hash = None
    filename = None

    def __init__(self, uri, hash):
        YpkgSource.__init__(self)
        self.uri = uri
        self.filename = os.path.basename(uri)
        self.hash = hash

    def __str__(self):
        return "%s (%s)" % (self.uri, self.hash)

    def _get_full_path(self, context):
        bpath = os.path.join(context.get_sources_directory(),
                             self.filename)
        return bpath

    def fetch(self, context):
        console_ui.emit_error("Source", "Fetch not yet implemented")
        return False

    def verify(self, context):
        bpath = self._get_full_path(context)

        hash = None

        with open(bpath, "r") as inp:
            h = hashlib.sha256()
            h.update(inp.read())
            hash = h.hexdigest()
        if hash != self.hash:
            console_ui.emit_error("Source", "Incorrect hash for {}".
                                  format(self.filename))
            print("Found hash    : {}".format(hash))
            print("Expected hash : {}".format(self.hash))
            return False
        return True

    def extract(self, context):
        console_ui.emit_error("Source", "Extract not yet implemented")
        return False

    def remove(self, context):
        console_ui.emit_error("Source", "Remove not yet implemented")
        return False

    def cached(self, context):
        bpath = self._get_full_path(context)
        return os.path.exists(bpath)


class SourceManager:
    """ Responsible for identifying, fetching, and verifying sources as listed
        within a YpkgSpec. """

    sources = None

    def __init__(self):
        self.sources = list()

    def identify_sources(self, spec):
        if not spec:
            return False

        for source in spec.pkg_source:
            if not isinstance(source, dict):
                console_ui.emit_error("SOURCE",
                                      "Source lines must be of 'key : value' "
                                      "mapping type")
                print("Erronous line: {}".format(str(source)))
                return False

            if len(source.keys()) != 1:
                console_ui.emit_error("SOURCE",
                                      "Encountered too many keys in source")
                print("Erronous source: {}".format(str(source)))
                return False

            uri = source.keys()[0]
            hash = source[uri]
            # TODO: Validate the URI, support more schemes..
            self.sources.append(TarSource(uri, hash))

        return True
