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

    option_group_format = parser.add_default_format_options()
    option_group_format.add_option("-r", "--root", action = "store_true",
            dest = "root", default = False,
            help = "Add ROOT as prefix to paths.")
    option_group_format.add_option("-t", "--target", action = "store_true",
            dest = "print_symlink_target", default = False,
            help = "Print targets for symlinks")

    # Listing Entries
    parser.add_default_content_limit_options()

    #{{{Matching by repository
    option_group_repo = OptionGroup(parser, "Matching by repository")
    option_group_repo.add_option("-R", "--repository", action = "append",
            dest = "source_repos", default=list(), metavar="REPO",
            help = """Match packages by source repository.
This option can be passed more than once to match more repositories.""")
    parser.add_option_group(option_group_repo)
    #}}}

    # Add default query options
    parser.add_default_query_options()

    options, args = parser.parse_args()

    #{{{Sanity Check
    # Check if any positional arguments are specified
    if not args:
        print >>sys.stderr, "Usage error: No package specified"
        print >>sys.stderr, "Try %s --help" % parser.get_prog_name()
        sys.exit(1)
    #}}}

    return options, args
#}}}

def main(): #{{{
    options, args = parse_command_line()
    env = EnvironmentMaker.instance.make_from_spec(options.environment)

    if options.colour:
        from putils.colours import colourify_content
    else:
        from putils.colours import no_colourify_content as colourify_content

    canonical_form = getattr(PackageIDCanonicalForm, options.canonical.upper())

    for package in args:
        content_generator = get_contents(package, env, options.source_repos,
                options.requested_instances, options.selection,
                options.fnpattern, options.regexp, options.ignore_case)

        for package_id, contents in content_generator:
            if options.colour:
                print "\033[1;35m*\033[0m",
            else:
                print "*",
            print package_id.canonical_form(canonical_form)
            for content in contents:
                if options.root:
                    print colourify_content(content, root),
                else:
                    print colourify_content(content),

                if options.print_symlink_target and hasattr(content, "target"):
                    print "->",
                    if options.root:
                        print colourify_content(content, root, target=True)
                    else:
                        print colourify_content(content, target=True)
                else:
                    print
#}}}

if __name__ == '__main__':
    main()
