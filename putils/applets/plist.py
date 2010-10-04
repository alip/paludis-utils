#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 sts=4 et tw=80 fdm=indent :
#
# Copyright (c) 2008 Ali Polatel <alip@exherbo.org>
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

from __future__ import print_function

import os
import sys
from optparse import OptionGroup

from paludis import (EnvironmentFactory, PackageIDCanonicalForm,
        Log, LogLevel, LogContext)

from putils.getopt import PaludisOptionParser
from putils.content import get_contents
from putils.util import setup_pager

__all__ = [ "main", "usage" ]

usage = """%prog [options] <pkgname>
List contents of packages matching requirements"""

def parse_command_line():
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

    # Matching by repository
    option_group_repo = OptionGroup(parser, "Matching by repository")
    option_group_repo.add_option("-R", "--repository", action = "append",
            dest = "source_repos", default=list(), metavar="REPO",
            help = """Match packages by source repository.
This option can be passed more than once to match more repositories.""")
    parser.add_option_group(option_group_repo)

    # Add default query options
    parser.add_default_query_options()

    options, args = parser.parse_args()

    # Check if any positional arguments are specified
    if not args:
        parser.error("No package specified")

    return options, args

def main():
    options, args = parse_command_line()
    env = EnvironmentFactory.instance.create(options.environment)
    proc, outfd = setup_pager()

    if proc is not None and options.colour:
        from putils.colours import colourify_content
    else:
        from putils.colours import no_colourify_content as colourify_content

    for package in args:
        content_generator = get_contents(package, env, options.source_repos,
                options.requested_instances, options.selection,
                options.fnpattern, options.regexp, options.ignore_case)

        for package_id, contents in content_generator:
            if proc is not None and options.colour:
                print("\033[1;35m*\033[0m", end=' ', file=outfd)
            else:
                print("*", end=' ', file=outfd)
            print(package_id.canonical_form(PackageIDCanonicalForm.FULL),
                    file=outfd)
            for content in contents:
                if options.root or env.root == os.path.sep:
                    print(colourify_content(content, env.root), end='',
                            file=outfd)
                else:
                    print(colourify_content(content, env.root), end='',
                            file=outfd)

                if options.print_symlink_target and hasattr(content, "target_key"):
                    print(" ->", end=' ', file=outfd)
                    if options.root or env.root == os.path.sep:
                        print(colourify_content(content, env.root, target=True),
                                file=outfd)
                    else:
                        print(colourify_content(content, env.root,
                                target=True).replace(env.root, ""), file=outfd)
                else:
                    print(file=outfd)

    if proc is not None:
        outfd.close()
        return proc.wait()

if __name__ == '__main__':
    main()

