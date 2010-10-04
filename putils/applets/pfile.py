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

"""List packages owning files
"""

from __future__ import print_function

import sys
from optparse import OptionGroup

from paludis import EnvironmentFactory

from putils.getopt import PaludisOptionParser
from putils.content import search_contents
from putils.util import setup_pager

__all__ = [ "main", "usage" ]

usage = """%prog [options] <filename>
List packages owning files"""

def parse_command_line():
    """Parse command line options."""

    parser = PaludisOptionParser()
    parser.usage = usage.replace("<filename>", "<filename>...")

    parser.add_default_format_options()
    parser.add_default_content_limit_options()

    option_group_query = OptionGroup(parser, "Query Options")
    option_group_query.add_option("-M", "--matcher", dest = "matcher",
            type = "choice", default = "exact", metavar="ALG",
            choices = [ "regex", "fnmatch", "simple", "exact" ],
            help = """Which match algorithm to use.
One of regex, fnmatch, simple, exact. Default: %default""")
    option_group_query.add_option("-i", "--ignore-case", action = "store_true",
            dest = "ignore_case",
            help = "Ignore case distinctions for matchers regex and fnmatch")

    parser.add_option_group(option_group_query)

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

    for filename in args:
        content_generator = search_contents(filename, env, options.matcher,
                options.ignore_case, options.requested_instances)

        for package_id, content in content_generator:
            print(package_id, colourify_content(content), file=outfd)

    if proc is not None:
        outfd.close()
        return proc.wait()

if __name__ == '__main__':
    main()

