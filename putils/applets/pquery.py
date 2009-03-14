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

    for package in args:
        remote_ids = get_ids(env, package, options.include_masked)
        for name, version, mkey in remote_ids:
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
                    if options.colour:
                        print("\033[1;35mN\033[0m", end=' ')
                    else:
                        print("N", end=' ')
                    print("%s-%s < %s-%s (%s)" % (name, version,
                            name, version_new, value))
                elif version_new == version:
                    if options.colour:
                        print("\033[0;32mE\033[0m", end=' ')
                    else:
                        print("E", end=' ')
                    print("%s-%s = %s-%s (%s)" % (name, version,
                            name, version_new, value))
                else:
                    if options.colour:
                        print("\033[1;31mO\033[0m", end=' ')
                    else:
                        print("O", end=' ')
                    print("%s-%s > %s-%s (%s)" % (name, version,
                            name, version_new, value))

if __name__ == '__main__':
    main()
