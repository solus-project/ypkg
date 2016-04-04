#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  This file is part of ypkg2
#
#  Copyright 2015-2016 Ikey Doherty <ikey@solus-project.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#

from . import console_ui


class TarSource:
    """ Represents a simple tarball source """
    uri = None
    hash = None

    def __init__(self, uri, hash):
        self.uri = uri
        self.hash = hash

    def __str__(self):
        return "%s (%s)" % (self.uri, self.hash)


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
