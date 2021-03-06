#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 sts=4 et tw=80 fdm=marker fmr={{{,}}}:
#
# Copyright (c) 2008, 2010 Ali Polatel <alip@exherbo.org>
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

"""Package content related functions
"""

from __future__ import generators

import os
import fnmatch
import re

from paludis import (Filter, Generator, Log, LogLevel, LogContext,
        MatchPackageOptions, Selection, VersionSpec, UserPackageDepSpecOption,
        parse_user_package_dep_spec)

from putils.util import rootjoin

__all__ = [ "get_contents", "search_contents" ]

def get_contents(package, env, source_repos = [],
        requested_instances = [object],
        selection = Selection.AllVersionsGroupedBySlot,
        fnpattern = None, regexp = None, ignore_case = False):
    """Get contents of package"""

    #{{{Pattern matching
    if regexp is not None:
        if ignore_case:
            pattern = re.compile(regexp, re.IGNORECASE)
        else:
            pattern = re.compile(regexp)
    #}}}

    #{{{Get PackageDepSpec
    filter_installed = Filter.InstalledAtRoot(env.system_root_key)
    allow_wildcards = UserPackageDepSpecOption.ALLOW_WILDCARDS
    package_dep_spec = parse_user_package_dep_spec(package, env,
            [allow_wildcards], filter_installed)
    #}}}

    #{{{Get CONTENTS
    ids = env[selection(Generator.Matches(package_dep_spec, MatchPackageOptions()) | filter_installed)]

    for package_id in ids:
        if package_id.contents_key() is None:
            Log.instance.message("vdb.no_contents", LogLevel.WARNING,
                    LogContext.NO_CONTEXT,
                    "'%s' does not provide a contents key." % package_id.name)
        else:
            #{{{Match by source repository
            if source_repos:
                if package_id.from_repositories_key() is None:
                    Log.instance.message("vdb.no_source_origin",
                            LogLevel.WARNING, LogContext.NO_CONTEXT,
                            "'%s' does not provide a from repositories key." % package_id.name)
                else:
                    repo_origin = package_id.from_repositories_key()

                    if not any(repo in source_repos for repo in
                            repo_origin.parse_value()):
                        continue
            #}}}

            requested_contents = list()
            for content in package_id.contents_key().parse_value():
                if not any([isinstance(content, i) for i in
                    requested_instances]):
                    continue

                content_path = rootjoin(content.location_key().parse_value(), env.root)

                if fnpattern is not None:
                    if ignore_case:
                        if not fnmatch.fnmatchcase(content_path, fnpattern):
                            continue
                    else:
                        if not fnmatch.fnmatch(content_path, fnpattern):
                            continue
                if regexp is not None and pattern.search(content_path) is None:
                    continue
                requested_contents.append(content)

            yield package_id, requested_contents
    #}}}
#}}}

def search_contents(path, env, matcher="exact", ignore_case=False, #{{{
        requested_instances=[object]):
    """Search filename in contents of installed packages."""

    # Get package ids of all installed packages
    ids = env[Selection.AllVersionsGroupedBySlot(
        Generator.Matches.All() | Filter.InstalledAtRoot(env.root)
        )]

    if matcher == "fnmatch":
        if ignore_case:
            fnmatch_matcher = fnmatch.fnmatchcase
        else:
            fnmatch_matcher = fnmatch.fnmatch
    elif matcher == "regex":
        if ignore_case:
            regex_matcher = re.compile(path, re.IGNORECASE)
        else:
            regex_matcher = re.compile(path)

    for package_id in ids:
        if package_id.contents_key() is None:
            Log.instance.message("vdb.no_contents", LogLevel.WARNING,
                    LogContext.NO_CONTEXT,
                    "'%s' does not provide a contents key." % package_id.name)
        else:
            for content in package_id.contents_key().parse_value():
                if not True in [isinstance(content, i) for i in
                        requested_instances]:
                    continue

                content_path = rootjoin(content.location_key().parse_value(), env.root)

                if (matcher == "exact" and
                        (path == content_path or
                            path == os.path.basename(content_path))):
                    yield package_id, content
                elif matcher == "simple" and path in content_path:
                    yield package_id, content
                elif (matcher == "fnmatch" and
                        fnmatch_matcher(content_path, path)):
                    yield package_id, content
                elif matcher == "regex" and regex_matcher.search(content_path):
                    yield package_id, content
#}}}
