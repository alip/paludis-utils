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

from urllib import urlretrieve
from xml.etree.cElementTree import iterparse

from paludis import (Filter, Generator, Selection, MatchPackageOptions,
        UserPackageDepSpecOption, parse_user_package_dep_spec)
from paludis import (VersionSpec, BadVersionSpecError)
from paludis import (Log, LogContext, LogLevel)

__all__ = [ "get_ids", "get_handler" ]

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
                except BadVersionSpecError as err:
                    Log.instance.message("freshmeat.bad_version",
                            LogLevel.WARNING, LogContext.NO_CONTEXT,
                            "Freshmeat has bad version for id '%s': %s" % id, err.message)
                    return None
    if version_new is None:
        Log.instance.message("freshmeat.no_version",
                LogLevel.WARNING, LogContext.NO_CONTEXT,
                "Freshmeat has no latest version information for id '%s'" % id)
        return None
    else:
        return version_new
