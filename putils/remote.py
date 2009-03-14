#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 sts=4 et tw=80 fdm=indent :
#
# Copyright (c) 2009 Ali Polatel <polatel@gmail.com>
#
# This file is part of the paludis-utils. paludis-utils is free software; you
# can redistribute it and/or modify it under the terms of the GNU General
# Public License version 2, as published by the Free Software Foundation.
#
# paludis-utils is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place, Suite 330, Boston, MA  02111-1307  USA

"""REMOTE_IDS support
"""

from __future__ import with_statement

import re
from urllib import urlretrieve
from xml.etree.cElementTree import iterparse
from subprocess import Popen, PIPE

from paludis import (Filter, Generator, Selection, MatchPackageOptions,
        UserPackageDepSpecOption, VersionSpec, parse_user_package_dep_spec)
from paludis import (Log, LogContext, LogLevel)

__all__ = [ "get_ids", "get_handler" ]

VIM_VERSION = re.compile("<td class=\"rowodd\" valign=\"top\" nowrap><b>(.*?)</b></td>")
GEM_VERSION = re.compile("\((.*?)\)")

def get_ids(env, package, include_masked):
    if include_masked:
        pfilter = Filter.All()
    else:
        pfilter = Filter.NotMasked()

    pds = parse_user_package_dep_spec(package, env,
            [UserPackageDepSpecOption.ALLOW_WILDCARDS], pfilter)
    pids = env[Selection.BestVersionOnly(
        Generator.Matches(pds, MatchPackageOptions()) | pfilter
        )]
    rids = []
    for pid in pids:
        mkey = pid.find_metadata("REMOTE_IDS")
        if mkey is not None:
            values = mkey.value()
            rids.append((pid.name, pid.version, values))
        else:
            Log.instance.message("e.no_remote_ids", LogLevel.WARNING,
                    LogContext.NO_CONTEXT,
                    "'%s' does not have a remote ids metadata key" % pid.name)
    return rids

def get_handler(remote):
    if remote == "freshmeat":
        return freshmeat
    elif remote == "pypi":
        return pypi
    elif remote == "cpan":
        return cpan
    elif remote == "vim":
        return vim
    elif remote == "rubyforge":
        return rubyforge
    else:
        return None

def freshmeat(id):
    version_new = None
    uri = "http://freshmeat.net/projects-xml/%s/%s.xml" % (id, id)
    filename, headers = urlretrieve(uri)
    with open(filename, "r") as f:
        for event, elem in iterparse(f):
            if elem.tag == "latest_release_version":
                try:
                    version_new = VersionSpec(elem.text)
                    break
                except:
                    Log.instance.message("freshmeat.bad_version",
                            LogLevel.WARNING, LogContext.NO_CONTEXT,
                            "freshmeat has bad version for id '%s': '%s'" % (id,
                                elem.text))
                    return None
    if version_new is None:
        Log.instance.message("freshmeat.no_version",
                LogLevel.WARNING, LogContext.NO_CONTEXT,
                "freshmeat has no latest version information for id '%s'" % id)
        return None
    else:
        return version_new

def pypi(id):
    version_new = None
    uri = "http://pypi.python.org/pypi?:action=doap&name=%s" % id
    filename, headers = urlretrieve(uri)
    with open(filename, "r") as f:
        for event, elem in iterparse(f):
            if elem.tag.endswith("revision"):
                try:
                    version_new = VersionSpec(elem.text)
                except:
                    Log.instance.message("pypi.bad_version",
                            LogLevel.WARNING, LogContext.NO_CONTEXT,
                            "pypi has bad version for id '%s': '%s'" % (id,
                            elem.text))
                    return None
    if version_new is None:
        Log.instance.message("pypi.no_version",
                LogLevel.WARNING, LogContext.NO_CONTEXT,
                "pypi has no latest version information for id '%s'" % id)
        return None
    else:
        return version_new

def cpan(id):
    version_new = None
    uri = "http://search.cpan.org/search?mode=module&format=xml&query=%s" % id
    filename, headers = urlretrieve(uri)
    with open(filename, "r") as f:
        seen_id = False
        for event, elem in iterparse(f):
            if elem.tag == "name" and elem.text == id:
                seen_id = True
            if seen_id and elem.tag == "version":
                try:
                    version_new = VersionSpec(elem.text)
                    break
                except:
                    Log.instance.message("cpan.bad_version",
                            LogLevel.WARNING, LogContext.NO_CONTEXT,
                            "cpan has bad version for id '%s': '%s'" % (id,
                            elem.text))
                    return None
    if version_new is None:
        Log.instance.message("cpan.no_version",
                LogLevel.WARNING, LogContext.NO_CONTEXT,
                "cpan has no latest version information for id '%s'" % id)
        return None
    else:
        return version_new

def vim(id):
    version_new = None
    uri = "http://www.vim.org/scripts/script.php?script_id=%s" % id
    filename, headers = urlretrieve(uri)
    with open(filename, "r") as f:
        m = VIM_VERSION.search(f.read())
        if m is not None:
            try:
                version_new = VersionSpec(m.groups()[0])
            except:
                Log.instance.message("vim.bad_version",
                        LogLevel.WARNING, LogContext.NO_CONTEXT,
                        "vim.org has bad version for id '%s': '%s'" % (id,
                        m.groups()[0]))
                return None
    if version_new is None:
        Log.instance.message("vim.no_version",
                LogLevel.WARNING, LogContext.NO_CONTEXT,
                "vim.org has no latest version information for id '%s'" % id)
        return None
    else:
        return version_new

def rubyforge(id):
    version_new = None
    gem = Popen(["gem", "search", id, "--remote"], stdout = PIPE, stderr = PIPE)
    out, err = gem.communicate()
    ret = gem.wait()
    if 0 != ret:
        Log.instance.message("rubyforge.exec_gem",
                LogLevel.WARNING, LogContext.NO_CONTEXT,
                "gem search returned non-zero: %s" % err)
        return None
    for line in out.splitlines():
        if line.startswith(id):
            m = GEM_VERSION.search(line)
            if m is not None:
                try:
                    version_new = VersionSpec(m.groups()[0])
                    break
                except:
                    Log.instance.message("rubyforge.bad_version",
                            LogLevel.WARNING, LogContext.NO_CONTEXT,
                            "rubyforge has bad version for id '%s': '%s'" % (id,
                                m.groups()[0]))
                    return None
    if version_new is None:
        Log.instance.message("rubyforge.no_version",
                LogLevel.WARNING, LogContext.NO_CONTEXT,
                "rubyforge has no latest version information for id '%s'" % id)
        return None
    else:
        return version_new

