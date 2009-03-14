#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 sts=4 et tw=80 fdm=indent :
#
# Copyright (c) 2009 Ali Polatel <polatel@gmail.com>
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

"""Query for package updates using REMOTE_IDS
"""

from __future__ import print_function

from sys import stderr
from optparse import OptionGroup
from paludis import EnvironmentFactory, Log, LogContext, LogLevel

from putils.getopt import PaludisOptionParser
from putils.remote import get_ids, get_handler

__all__ = [ "main", "usage" ]

usage = """%prog [options] <pkgname>
Query for package updates using REMOTE_IDS"""

ESC    = "\033["
NORM   = ESC + "0m"
PINK   = ESC + "1;35m"
GREEN  = ESC + "0;32m"
RED    = ESC + "1;31m"
BROWN  = ESC + "0;33m"
YELLOW = ESC + "1;33m"

def parse_command_line():
    """Parse command line options."""

    parser = PaludisOptionParser()
    parser.usage = usage.replace("<pkgname>", "<pkgname>...")

    parser.add_default_format_options()
    fgroup = OptionGroup(parser, "Filtering Options")
    fgroup.add_option("-i", "--include-masked", action = "store_true", dest =
        "include_masked",
        help = "Include masked packages")
    parser.add_option_group(fgroup)

    options, args = parser.parse_args()

    # Check if any positional arguments are specified
    if not args:
        parser.error("No package specified")

    return options, args

def main():
    options, args = parse_command_line()
    env = EnvironmentFactory.instance.create(options.environment)

    if options.colour:
        global NORM, PINK, GREEN, RED, BROWN, YELLOW
    else:
        NORM = PINK = GREEN = RED = BROWN = YELLOW = ""

    for package in args:
        for name, version, mkey in get_ids(env, package, options.include_masked):
            for value in mkey:
                remote, id = str(value).split(":", 1)
                handler = get_handler(remote)
                if handler is None:
                    Log.instance.message("remote.no_handler", LogLevel.WARNING,
                            LogContext.NO_CONTEXT,
                            "No handler for remote '%s'" % remote)
                    continue

                version_new = handler(id)
                if version_new is None:
                    continue
                elif version_new > version:
                    print(PINK + "N" + NORM, end=' ')
                    print("%s-{%s%s < %s%s} %s%s%s" % (name, PINK, version,
                            version_new, NORM, BROWN, value, NORM))
                elif version_new == version:
                    print(GREEN + "E" + NORM, end=' ')
                    print("%s-{%s%s = %s%s} %s%s%s" % (name, GREEN, version,
                            version_new, NORM, BROWN, value, NORM))
                else:
                    print(RED + "O" + NORM, end=' ')
                    print("%s-{%s%s > %s%s} %s%s%s" % (name, RED, version,
                            version_new, NORM, BROWN, value, NORM))

if __name__ == '__main__':
    main()
