#!/bin/true
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
import subprocess
import fnmatch
import shutil

KnownSourceTypes = {
    'tar': [
        '*.tar.*',
        '*.tgz',
    ],
    'zip': [
        '*.zip',
    ],
}


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


class GitSource(YpkgSource):
    """ Provides git source support to ypkg """

    # Source URI
    uri = None

    # Tag or branch to check out
    tag = None

    def __init__(self, uri, tag):
        YpkgSource.__init__(self)
        self.uri = uri
        self.tag = tag
        self.filename = self.get_target_name()

    def __str__(self):
        return "{} ({})".format(self.uri, self.tag)

    def is_dumb_transport(self):
        """ Http depth cloning = no go """
        if self.uri.startswith("http:") or self.uri.startswith("https:"):
            return True
        return False

    def get_target_name(self):
        """ Get the target directory base name after its fetched """
        uri = str(self.uri)
        if uri.endswith(".git"):
            uri = uri[:-4]
        return os.path.basename(uri) + ".git"

    def get_full_path(self, context):
        """ Fully qualified target path """
        return os.path.join(context.get_sources_directory(),
                            self.get_target_name())

    def fetch(self, context):
        """ Clone the actual git repo, favouring efficiency... """
        source_dir = context.get_sources_directory()

        # Ensure source dir exists
        if not os.path.exists(source_dir):
            try:
                os.makedirs(source_dir, mode=00755)
            except Exception as e:
                console_ui.emit_error("Source", "Cannot create sources "
                                      "directory: {}".format(e))
                return False

        cmd = "git -C \"{}\" clone --recursive \"{}\" {}".format(
            source_dir, self.uri, self.get_target_name())

        console_ui.emit_info("Git", "Fetching: {}".format(self.uri))
        try:
            r = subprocess.check_call(cmd, shell=True)
        except Exception as e:
            console_ui.emit_error("Git", "Failed to fetch {}".format(
                                  self.uri))
            print("Error follows: {}".format(e))
            return False

        console_ui.emit_info("Git", "Checking out: {}".format(self.tag))
        cmd = "git -C \"{}\" checkout \"{}\"".format(
            os.path.join(source_dir, self.get_target_name()),
            self.tag)
        try:
            r = subprocess.check_call(cmd, shell=True)
        except Exception as e:
            console_ui.emit_error("Git", "Failed to checkout {}".format(
                                  self.tag))
            return False
        return True

    def verify(self, context):
        """ Verify source = good. """
        bpath = self.get_full_path(context)

        status_cmd = "git -C {} diff --exit-code"
        try:
            subprocess.check_call(status_cmd.format(bpath), shell=True)
        except Exception:
            console_ui.emit_error("Git", "Unexpected diff in source")
            return False
        return True

    def extract(self, context):
        """ Extract ~= copy source into build area. Nasty but original source
            should not be tainted between runs.
        """

        source = self.get_full_path(context)
        target = os.path.join(context.get_build_dir(),
                              self.get_target_name())

        if os.path.exists(target):
            try:
                shutil.rmtree(target)
            except Exception as e:
                console_ui.emit_error("Git", "Cannot remove stagnant tree")
                print(e)
                return False

        if not os.path.exists(context.get_build_dir()):
            try:
                os.makedirs(context.get_build_dir(), mode=00755)
            except Exception as e:
                console_ui.emit_error("Source", "Cannot create sources "
                                      "directory: {}".format(e))
                return False
        try:
            shutil.copytree(source, target)
        except Exception as e:
            console_ui.emit_error("Git", "Failed to copy source to build")
            print(e)
            return False
        return True

    def cached(self, context):
        bpath = self.get_full_path(context)
        return os.path.exists(bpath)


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
        source_dir = context.get_sources_directory()

        # Ensure source dir exists
        if not os.path.exists(source_dir):
            try:
                os.makedirs(source_dir, mode=00755)
            except Exception as e:
                console_ui.emit_error("Source", "Cannot create sources "
                                      "directory: {}".format(e))
                return False

        console_ui.emit_info("Source", "Fetching: {}".format(self.uri))
        fpath = self._get_full_path(context)
        cmd = "curl -o \"{}\" --url \"{}\" --location".format(
               fpath, self.uri)
        try:
            r = subprocess.check_call(cmd, shell=True)
        except Exception as e:
            console_ui.emit_error("Source", "Failed to fetch {}".format(
                                  self.uri))
            print("Error follows: {}".format(e))
            return False

        return True

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

        target = os.path.join(BallDir, os.path.basename(x))
        ext = "unzip" if target.endswith(".zip") else "tar xf"
        diropt = "-d" if target.endswith(".zip") else "-C"
        cmd = "%s \"%s\" %s \"%s\"" % (ext, target, diropt, bd)

    def get_extract_command_zip(self, context, bpath):
        """ Get a command tailored for zip usage """
        cmd = "unzip \"{}\" -d \"{}/\"".format(bpath, context.get_build_dir())
        return cmd

    def get_extract_command_tar(self, context, bpath):
        """ Get a command tailored for tar usage """
        cmd = "tar xf \"{}\" -C \"{}/\"".format(bpath, context.get_build_dir())
        return cmd

    def extract(self, context):
        """ Extract an archive into the context.get_build_dir() """
        bpath = self._get_full_path(context)

        # Grab the correct extraction command
        fileType = None
        for key in KnownSourceTypes:
            lglobs = KnownSourceTypes[key]
            for lglob in lglobs:
                if fnmatch.fnmatch(self.filename, lglob):
                    fileType = key
                    break
            if fileType:
                break

        if not fileType:
            console_ui.emit_warning("Source", "Type of file {} is unknown, "
                                    "falling back to tar handler".
                                    format(self.filename))
            fileType = "tar"

        cmd_name = "get_extract_command_{}".format(fileType)
        if not hasattr(self, cmd_name):
            console_ui.emit_error("Source", "Fatal error: No handler for {}".
                                  format(fileType))
            return False

        if not os.path.exists(context.get_build_dir()):
            try:
                os.makedirs(context.get_build_dir(), mode=00755)
            except Exception as e:
                console_ui.emit_error("Source", "Failed to construct build "
                                      "directory")
                print(e)
                return False

        cmd = getattr(self, cmd_name)(context, bpath)
        try:
            subprocess.check_call(cmd, shell=True)
        except Exception as e:
            console_ui.emit_error("Source", "Failed to extract {}".
                                  format(self.filename))
            return False
        return True

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
            # Check if its a namespaced support type
            if "|" in uri:
                brk = uri.split("|")
                # It's a git| prefix
                if brk[0] == 'git':
                    uri = "|".join(brk[1:])
                    self.sources.append(GitSource(uri, hash))
                    continue
            self.sources.append(TarSource(uri, hash))

        return True

    def _get_working_dir(self, context):
        """ Need to make this.. better. It's very tar-type now"""
        build_dir = context.get_build_dir()

        source0 = self.sources[0].filename
        if os.path.exists(build_dir):
            items = os.listdir(build_dir)
            if len(items) == 1:
                return os.path.join(build_dir, items[0])
            for item in items:
                if source0.startswith(item):
                    return os.path.join(build_dir, item)
            return build_dir
        else:
            return build_dir

    def get_working_dir(self, context):
        potential = self._get_working_dir(context)
        if not os.path.exists(potential) or not os.path.isdir(potential):
            return context.get_build_dir()
        return potential
