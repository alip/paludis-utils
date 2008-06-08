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

import os
import fnmatch
import re

from paludis import (ContentsDevEntry, ContentsDirEntry, ContentsFifoEntry,
        ContentsFileEntry, ContentsMiscEntry, ContentsSymEntry, Filter,
        Generator, Selection, VersionSpec, UserPackageDepSpecOption,
        QualifiedPackageNameError, parse_user_package_dep_spec)

__all__ = [ "compare_atoms", "get_contents", "split_cpv" ]

def get_contents(package, env, source_repos = [], only_directories = False,
        only_files = False, only_misc = False, only_symlink = False,
        only_dev = False, only_fifo = False,
        selection = "all-versions-grouped-by-slot", fnpattern = None,
        regexp = None, ignore_case = False):
    """Get contents of package"""

    #{{{Selection
    selection = "".join([x.capitalize() for x in selection.split("_")])
    selection = getattr(Selection, selection)
    #}}}

    #{{{Requested Instance
    if only_dev:
        requested_instance = ContentsDevEntry
    elif only_directories:
        requested_instance = ContentsDirEntry
    elif only_fifo:
        requested_instance = ContentsFifoEntry
    elif only_files:
        requested_instance = ContentsFileEntry
    elif only_misc:
        requested_instance = ContentsMiscEntry
    elif only_symlink:
        requested_instance = ContentsSymEntry
    else:
        requested_instance = object
    #}}}

    #{{{Pattern matching
    if regexp is not None:
        if ignore_case:
            pattern = re.compile(regexp, re.IGNORECASE)
        else:
            pattern = re.compile(regexp)
    #}}}

    #{{{Get PackageDepSpec
    filter_env = Filter.SupportsInstalledAction()
    allow_wildcards = UserPackageDepSpecOption.ALLOW_WILDCARDS
    try:
        package_dep_spec = parse_user_package_dep_spec(package,
                [allow_wildcards])
    except QualifiedPackageNameError, e:
        # Get a qualified package name
        qpn = env.package_database.fetch_unique_qualified_package_name(
                package, filter_env)
        package = str(qpn.category) + "/" + str(qpn.package)
        package_dep_spec = parse_user_package_dep_spec(package,
                [allow_wildcards])
    #}}}

    #{{{Get CONTENTS
    ids = env[selection(Generator.Matches(package_dep_spec) |
        filter_env)]

    contents = dict()
    for pkg_id in ids:
        if pkg_id.contents_key() is None:
            Log.instance.message("vdb.no_contents", LogLevel.WARNING,
                    LogContext.NO_CONTEXT,
                    "'%s' does not provide a contents key." % pkg_id.name)
        else:
            #{{{Match by source repository
            if source_repos:
                if pkg_id.source_origin_key() is None:
                    Log.instance.message("vdb.no_source_origin",
                            LogLevel.WARNING, LogContext.NO_CONTEXT,
                            "'%s' does not provide a source origin key." % pkg_id.name)
                else:
                    source_origin = pkg_id.source_origin_key()
                    if source_origin.value() not in source_repos:
                        continue
            #}}}
            contents[pkg_id] = []
            for c in pkg_id.contents_key().value():
                c_path = os.path.sep.join((env.root, c.name))
                if isinstance(c, requested_instance):
                    if fnpattern is not None:
                        if ignore_case:
                            if not fnmatch.fnmatchcase(c_path, fnpattern):
                                continue
                        else:
                            if not fnmatch.fnmatch(c_path, fnpattern):
                                continue
                    if regexp is not None and pattern.match(c_path) is None:
                        continue
                    contents[pkg_id].append(c)
    return contents
    #}}}
#}}}

def split_cpv(cpv): #{{{
    """Split a package into category, package, version, revision."""

    category = ""
    fake_category = "arnold-layne"
    cat_pn_sep = "/"
    version_re = re.compile("-\d")

    if cat_pn_sep not in cpv:
        # Make package name look like a qualified package name.
        cpv = cat_pn_sep.join((fake_category, cpv))
        category = None
    if version_re.search(cpv) and not cpv.startswith("="):
        # Make package name look like an exact version
        cpv = "=" + cpv

    if cpv.endswith("/"):
        category = re.sub("/+", "", cpv)
        return category, None, None, None

    package_dep_spec = parse_user_package_dep_spec(cpv, [])
    qpn = package_dep_spec.package

    if category is not None:
        category = str(qpn.category)

    package_name = str(qpn.package)

    # Split version and revision
    if cpv.startswith("="):
        cat_pkg = ""
        if category is not None:
            cat_pkg += category + cat_pn_sep
        else:
            cat_pkg += fake_category + cat_pn_sep

        cat_pkg += package_name
        cat_pkg_re = re.compile(r"=?%s-" % cat_pkg)

        version = cat_pkg_re.sub("", package_dep_spec.text)
        if version:
            version_spec = VersionSpec(version)
            revision = version_spec.revision_only()
            main_version = re.sub("-%s$" % revision, "", version)
        else:
            main_version = revision = None
    else:
        main_version = revision = None

    return category, package_name, main_version, revision
#}}}

def compare_atoms(first_atom, second_atom): #{{{
    """Compare two atoms

    @return: None if atoms aren't equal, 0 if atoms are equal, 1 if the first
        atom is greater, -1 if the second atom is greater.
    """

    category_1, name_1, version_1, revision_1 = split_cpv(first_atom)
    category_2, name_2, version_2, revision_2 = split_cpv(second_atom)

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
