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

"""List contents of packages matching requirements
"""

import os
import sys
from optparse import OptionGroup

from paludis import (EnvironmentMaker, PackageIDCanonicalForm,
        Log, LogLevel, LogContext)

from putils.getopt import PaludisOptionParser
from putils.packages import get_contents

__all__ = [ "main", "usage" ]

usage = """%prog [options] <pkgname>
List contents of packages matching requirements"""

def parse_command_line(): #{{{
    """Parse command line options."""

    parser = PaludisOptionParser()
    parser.usage = usage.replace("<pkgname>", "<pkgname>...")

    # Listing Entries
    parser.add_default_content_limit_options()

    #{{{Format options
    option_group_format = OptionGroup(parser, "Formatting Options")
    option_group_format.add_option("-r", "--root", action = "store_true",
            dest = "root", default = False,
            help = "Add ROOT as prefix to paths.")
    option_group_format.add_option("-t", "--target", action = "store_true",
            dest = "print_symlink_target", default = False,
            help = "Print targets for symlinks")
    parser.add_option_group(option_group_format)
    #}}}

    #{{{Add default query options
    parser.add_default_query_options()
    parser.add_default_advanced_query_options()
    #}}}

    (options, args) = parser.parse_args()

    #{{{Sanity Check
    # Check if any positional arguments are specified
    if not args:
        print >>sys.stderr, "Usage error: No package specified"
        print >>sys.stderr, "Try %s --help" % parser.get_prog_name()
        sys.exit(1)

    # Check for conflicting options
    may_conflict_options = {
            '--dir'     : options.only_directories,
            '--file'    : options.only_files,
            '--misc'    : options.only_misc,
            '--symlink' : options.only_symlink,
            '--device'  : options.only_dev,
            '--fifo'    : options.only_fifo }
    only_options_true = 0
    conflicting_options = []

    for opt in may_conflict_options:
        if may_conflict_options[opt]:
            conflicting_options.append(opt)
            only_options_true += 1

    if only_options_true > 1:
        print >>sys.stderr, "Usage error: Conflicting options:",
        print >>sys.stderr, ", ".join(conflicting_options)
        print >>sys.stderr, "Try %s --help" % parser.get_prog_name()
        sys.exit(1)

    if (conflicting_options and not '--symlink' in conflicting_options and
            options.print_symlink_target):
            Log.instance.message("cmdline.option_not_valid", LogLevel.WARNING,
                    LogContext.NO_CONTEXT,
                    "Option --target is only valid when listing symlinks")
    #}}}

    return (options, args)
#}}}

def main(): #{{{
    options, args = parse_command_line()
    env = EnvironmentMaker.instance.make_from_spec(options.environment)

    for package in args:
        contents = get_contents(package, env, options.only_directories,
                options.only_files, options.only_misc, options.only_symlink,
                options.only_dev, options.only_fifo, options.allow_wildcards,
                options.selection, options.fnpattern, options.regexp,
                options.ignore_case)
        for package_id in contents:
            print "*", package_id.canonical_form(PackageIDCanonicalForm.FULL)
            for c in contents[package_id]:
                if options.root:
                    print os.path.sep.join((env.root, c.name)),
                else:
                    print c.name,
                if options.print_symlink_target and hasattr(c, "target"):
                    print "->",
                    if options.root:
                        print os.path.sep.join((env.root, c.target))
                    else:
                        print c.target
                else:
                    print
#}}}

if __name__ == '__main__':
    main()
