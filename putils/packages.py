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

import fnmatch
import re

from paludis import (ContentsDevEntry, ContentsDirEntry, ContentsFifoEntry,
        ContentsFileEntry, ContentsMiscEntry, ContentsSymEntry, Filter,
        Generator, Selection, UserPackageDepSpecOption, PackageNamePartError,
        parse_user_package_dep_spec)

__all__ = [ "get_contents" ]

def get_contents(package, environment, only_directories = False, #{{{
        only_files = False, only_misc = False, only_symlink = False,
        only_dev = False, only_fifo = False,
        allow_wildcards = False, selection = "all-versions-grouped-by-slot",
        fnpattern = None, regexp = None, ignore_case = False):
    """Get contents of package"""

    #{{{Wildcards
    if allow_wildcards:
        parse_options = [UserPackageDepSpecOption.ALLOW_WILDCARDS]
    else:
        parse_options = []
    #}}}

    #{{{Selection
    selection = "".join([x.capitalize() for x in selection.split("-")])
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

    #{{{Get unique qpn
    try:
        qpn_obj = environment.package_database.fetch_unique_qualified_package_name(package)
        qpn = str(qpn_obj.category) + "/" + str(qpn_obj.package)
    except PackageNamePartError:
        qpn = package
    #}}}

    #{{{Get CONTENTS
    ids = environment[selection(
        Generator.Matches(
            parse_user_package_dep_spec(qpn, parse_options)) |
        Filter.SupportsInstalledAction())]

    contents = dict()
    for pkg_id in ids:
        if pkg_id.contents_key() is None:
            Log.instance.message("vdb.no_contents", LogLevel.WARNING,
                    LogContext.NO_CONTEXT,
                    "'%s' does not provide a contents key." % pkg_id.name)
        else:
            contents[pkg_id] = []
            for c in pkg_id.contents_key().value():
                if isinstance(c, requested_instance):
                    if fnpattern is not None:
                        if ignore_case:
                            if not fnmatch.fnmatchcase(c.name, fnpattern):
                                continue
                        else:
                            if not fnmatch.fnmatch(c.name, fnpattern):
                                continue
                    if regexp is not None and pattern.match(c.name) is None:
                        continue
                    contents[pkg_id].append(c)
    return contents
    #}}}
#}}}
