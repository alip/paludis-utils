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

"""Calculate size of installed packages.
"""

import os
import sys
from optparse import OptionGroup

from paludis import (ContentsDevEntry, ContentsDirEntry, ContentsFifoEntry,
        ContentsFileEntry, ContentsMiscEntry, ContentsSymEntry,
        Log, LogLevel, LogContext,
        EnvironmentMaker, PackageIDCanonicalForm)

from putils.getopt import PaludisOptionParser
from putils.packages import get_contents

__all__ = [ "main", "usage" ]

usage = """%prog [options] <pkgname>
Calculate size of installed packages"""

#{{{Globals
SIZE_MEGABYTES = float(1024 * 1024)
SIZE_KILOBYTES = float(1024)
SIZE_BYTES = float(1)

_total_stats = { "devices" : 0,
        "directories" : 0,
        "fifos" : 0,
        "files" : 0,
        "misc" : 0,
        "symlinks" : 0,
        "unknown" : 0 }
_total_size = 0
#}}}

def content_stat(contents, root, sum=False): #{{{
    """Return a statistics of contents."""

    stats = { "devices" : 0,
        "directories" : 0,
        "fifos" : 0,
        "files" : 0,
        "misc" : 0,
        "symlinks" : 0,
        "unknown" : 0 }
    size = 0

    for c in contents:
        if isinstance(c, ContentsDevEntry):
            stats["devices"] += 1
        elif isinstance(c, ContentsDirEntry):
            stats["directories"] += 1
        elif isinstance(c, ContentsFifoEntry):
            stats["fifos"] += 1
        elif isinstance(c, ContentsFileEntry):
            stats["files"] += 1
            c_path = os.path.sep.join((root, c.name))
            if os.path.exists(c_path):
                size += os.path.getsize(c_path)
            else:
                Log.instance.message("content.non_existant_file",
                        LogLevel.WARNING, LogContext.NO_CONTEXT,
                        "File \"%s\" doesn't exit!" % c_path)
        elif isinstance(c, ContentsMiscEntry):
            stats["misc"] += 1
        elif isinstance(c, ContentsSymEntry):
            stats["symlinks"] += 1
        else:
            stats["unknown"] += 1

    if sum:
        global _total_stats, _total_size
        for key in stats:
            _total_stats[key] += stats[key]
        _total_size += size

    return size, stats
#}}}

def pprint_contents(contents, root, divisor=1024.0, sum=False, sum_only=False): #{{{
    """Pretty print package contents."""

    if contents is None:
        # Print total
        global _total_stats, _total_size
        size, stats = _total_size, _total_stats
    else:
        size, stats = content_stat(contents, root, sum)
        if sum_only:
            return

    # Remove empty
    empty = []
    for key in stats:
        if not stats[key]:
            empty.append(key)
    for key in empty:
        del stats[key]

    for key in stats:
        print "%d %s," % (stats[key], key),

    size /= divisor
    print "%.2f" % size,
    if divisor == SIZE_MEGABYTES:
        print "MB"
    elif divisor == SIZE_KILOBYTES:
        print "KB"
    else:
        print "B"
#}}}

def parse_command_line(): #{{{
    """Parse command line options."""

    parser = PaludisOptionParser()
    parser.usage = usage.replace("<pkgname>", "<pkgname>...")

    og_size = OptionGroup(parser, "Displaying Size")
    og_size.add_option("-M","--megabytes", action = "store_const",
            const = SIZE_MEGABYTES, dest = "display_size",
            help = "Display size in megabytes")
    og_size.add_option("-K", "--kilobytes", action = "store_const",
            const = SIZE_KILOBYTES, dest = "display_size",
            help = "Display size in kilobytes (Default)")
    og_size.add_option("-B", "--bytes", action = "store_const",
            const = SIZE_BYTES, dest = "display_size",
            help = "Display size in bytes")
    parser.add_option_group(og_size)

    og_summary = OptionGroup(parser, "Summary")
    og_summary.add_option("", "--sum", action = "store_true",
            dest = "sum", default = False, help = "Include a summary")
    og_summary.add_option("", "--sum-only", action = "store_true",
            dest = "sum_only", default = False, help = "Show just the summary")
    parser.add_option_group(og_summary)

    parser.add_default_content_limit_options()

    #{{{Matching by repository
    option_group_repo = OptionGroup(parser, "Matching by repository")
    option_group_repo.add_option("-R", "--repository", action = "append",
            dest = "source_repos", default=list(), metavar="REPO",
            help = """Match packages by source repository.
This option can be passed more than once to match more repositories.""")
    parser.add_option_group(option_group_repo)
    #}}}

    parser.add_default_query_options()
    parser.add_default_advanced_query_options()

    options, args = parser.parse_args()

    # Check if any positional arguments are specified
    if not args:
        print >>sys.stderr, "Usage error: No package specified"
        print >>sys.stderr, "Try %s --help" % parser.get_prog_name()
        sys.exit(1)

    return options, args
#}}}

def main(): #{{{
    options, args = parse_command_line()
    env = EnvironmentMaker.instance.make_from_spec(options.environment)

    if options.display_size is None:
        options.display_size = SIZE_KILOBYTES

    for package in args:
        content_generator = get_contents(package, env, options.source_repos,
                options.requested_instances, options.selection,
                options.fnpattern, options.regexp, options.ignore_case)

        for package_id, contents in content_generator:
            print package_id.canonical_form(PackageIDCanonicalForm.FULL),
            pprint_contents(contents, env.root, options.display_size,
                    options.sum, options.sum_only)

    if options.sum or options.sum_only:
        print "Totals:",
        pprint_contents(None, env.root, options.display_size, options.sum,
                options.sum_only)
#}}}

if __name__ == '__main__':
    main()
