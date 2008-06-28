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

"""List packages owning files
"""

import sys
from optparse import OptionGroup

from paludis import EnvironmentMaker

from putils.getopt import PaludisOptionParser
from putils.packages import search_contents

__all__ = [ "main", "usage" ]

usage = """%prog [options] <filename>
List packages owning files"""

def parse_command_line(): #{{{
    """Parse command line options."""

    parser = PaludisOptionParser()
    parser.usage = usage.replace("<filename>", "<filename>...")

    parser.add_option("-C", "--no-colour", action = "store_false",
            dest = "colour", default = True,
            help = "Don't output colour")

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
        print >>sys.stderr, "Usage error: No package specified"
        print >>sys.stderr, "Try %s --help" % parser.get_prog_name()
        sys.exit(1)

    return options, args
#}}}

def main(config=None): #{{{
    options, args = parse_command_line()
    env = EnvironmentMaker.instance.make_from_spec(options.environment)

    if options.colour:
        from putils.colours import colourify_content
    else:
        from putils.colours import no_colourify_content as colourify_content

    for filename in args:
        content_generator = search_contents(filename, env, options.matcher,
                options.ignore_case, options.requested_instances)

        for package_id, content in content_generator:
            print package_id, colourify_content(content)
#}}}

if __name__ == '__main__':
    main()

