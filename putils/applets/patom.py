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

"""Split atom strings
"""

import sys
import re

from paludis import EnvironmentMaker

from putils.getopt import PaludisOptionParser
from putils.packages import compare_atoms, split_atom

__all__ = [ "main", "usage" ]

usage = """%prog [options] <pkgname>
Split atom strings"""

DEFAULT_MISSING_PART = "(null)"

def parse_command_line(): #{{{
    """Parse command line options."""

    parser = PaludisOptionParser()
    parser.usage = usage.replace("<pkgname>", "<pkgname>...")

    parser.add_option("-c", "--compare", action = "store_true",
            dest = "compare", default = False,
            help = "Compare two atoms")
    parser.add_option("-m", "--missing", action = "store",
            dest = "missing", default = DEFAULT_MISSING_PART,
            help = "String to print for missing parts")

    options, args = parser.parse_args()

    # Check if any positional arguments are specified
    if not args:
        print >>sys.stderr, "Usage error: No package specified"
        print >>sys.stderr, "Try %s --help" % parser.get_prog_name()
        sys.exit(1)
    if options.compare and len(args) != 2:
        print >>sys.stderr, "Usage error: Wrong number of arguments"
        print >>sys.stderr, "Try %s --help" % parser.get_prog_name()
        sys.exit(1)

    return options, args

def main(): #{{{
    options, args = parse_command_line()
    env = EnvironmentMaker.instance.make_from_spec(options.environment)

    if options.compare:
        ret = compare_atoms(args[0], args[1], env)
        if ret is None:
            print args[0], "!=", args[1]
        elif ret == 0:
            print args[0], "==", args[1]
        elif ret == 1:
            print args[0], ">", args[1]
        elif ret == -1:
            print args[0], "<", args[1]
    else:
        for package in args:
            category, package_name, version, revision = split_atom(package, env)
            for part in (category, package_name, version, revision):
                if part is not None:
                    print part,
                else:
                    print options.missing,
            print
#}}}

if __name__ == '__main__':
    main()
