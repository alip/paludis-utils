#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 sts=4 et tw=80 fdm=marker fmr={{{,}}}:
#
# Copyright (c) 2008 Ali Polatel <polatel@itu.edu.tr>
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

"""Package related functions
"""

from __future__ import generators

import os
import fnmatch
import re

from paludis import (Filter, Generator, Log, LogLevel, LogContext, Selection,
        VersionSpec, UserPackageDepSpecOption, QualifiedPackageNameError,
        parse_user_package_dep_spec)

from putils.compat import any

__all__ = [ "abspath", "compare_atoms", "get_contents", "search_contents", "split_atom" ]

PMS_VERSION = re.compile("""
    (?P<main_version>
        (?P<bare_version>\d+(\.\d+)*)
        (?P<letter>[a-z])?
        (?P<suffix>_alpha|_beta|_pre|_rc|_p(\d+)?)?
    )
    (-(?P<revision>r\d+))?""", re.VERBOSE)


def abspath(path, root):
    """If root is / then return path,
    else return root + / + path."""
    if root == os.path.sep:
        return path
    else:
        return os.path.sep.join((root, path))

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
    filter_installed = Filter.SupportsInstalledAction()
    allow_wildcards = UserPackageDepSpecOption.ALLOW_WILDCARDS
    package_dep_spec = parse_user_package_dep_spec(package, env,
            [allow_wildcards], filter_installed)
    #}}}

    #{{{Get CONTENTS
    ids = env[selection(Generator.Matches(package_dep_spec) |
        filter_installed)]

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

                    repo_found = False
                    for repo in repo_origin.value():
                        if repo in source_repos:
                            repo_found = True
                            break

                    if not repo_found:
                        continue
            #}}}

            requested_contents = list()
            for content in package_id.contents_key().value():
                if not any([isinstance(content, i) for i in
                    requested_instances]):
                    continue

                content_path = abspath(content.name, env.root)
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
        Generator.Matches.All() | Filter.SupportsInstalledAction()
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
            for content in package_id.contents_key().value():
                if not True in [isinstance(content, i) for i in
                        requested_instances]:
                    continue

                content_path = abspath(content.name, env.root)

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

def split_atom(atom, env): #{{{
    """Split an atom into category, package, version, revision."""

    global PMS_VERSION

    category = ""
    fake_category = "arnold-layne"
    cat_pn_sep = "/"

    if cat_pn_sep not in atom:
        # Make package name look like a qualified package name.
        atom = cat_pn_sep.join((fake_category, atom))
        category = None
    if PMS_VERSION.search(atom) and not atom.startswith("="):
        # Make package name look like an exact version
        atom = "=" + atom

    if atom.endswith("/"):
        category = re.sub("/+", "", atom)
        return category, None, None, None

    package_dep_spec = parse_user_package_dep_spec(atom, env, [])
    qpn = package_dep_spec.package

    if category is not None:
        category = str(qpn.category)

    package_name = str(qpn.package)

    # Split version and revision
    if atom.startswith("="):
        version = PMS_VERSION.search(package_dep_spec.text)

        if version is not None:
            main_version = version.group("main_version")
            if version.group("revision"):
                revision = version.group("revision")
            else:
                revision = "r0"
        else:
            main_version = revision = None
    else:
        main_version = revision = None

    return category, package_name, main_version, revision
#}}}

def compare_atoms(first_atom, second_atom, env): #{{{
    """Compare two atoms

    @return: None if atoms aren't equal, 0 if atoms are equal, 1 if the first
        atom is greater, -1 if the second atom is greater.
    """

    category_1, name_1, version_1, revision_1 = split_atom(first_atom, env)
    category_2, name_2, version_2, revision_2 = split_atom(second_atom, env)

    if category_1 != category_2 or name_1 != name_2:
        return None
    elif (version_1 is None and version_2 is not None or
            version_1 is not None and version_2 is None):
        return None
    elif None in (version_1, version_2):
        return 0
    else:
        version_spec_1 = VersionSpec("-".join((version_1, revision_1)))
        version_spec_2 = VersionSpec("-".join((version_2, revision_2)))

        if version_spec_1 > version_spec_2:
            return 1
        elif version_spec_1 == version_spec_2:
            return 0
        else:
            return -1
#}}}
