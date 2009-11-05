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

import re
from sys import stderr
from optparse import OptionGroup
from paludis import EnvironmentFactory, Log, LogContext, LogLevel

from putils.getopt import PaludisOptionParser
from putils.remote import get_ids, get_handler
from putils.util import setup_pager

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

def parse_auth_data(auth_data):
    """Parse serialised remote authorization data into a dict for querying by
    remote handler functions that require some form of authorization, e.g.
    putils.remote.freshmeat().

    The serialisation format is a single string of semicolon-delimited fields
    containing key=value pairs. A literal semicolon is allowed in a key or
    value if it is escaped with a '\' character. A literal '=' character is
    allowed in a value unescaped, but not allowed in a key whether escaped or
    unescaped. The '\' character is allowed in keys and values and is stored
    (and returned) by the dict as an escaped literal.

    The returned dict contains parsed keys and values stripped of leading and
    trailing whitespace. A field from the serialised string is silently omitted
    from the dict if not recognised as being of the form key=value, while
    stricter parsing errors cause pquery to exit with an error message."""

    if not auth_data:
        return None

    try:
        pairs = [ map(str.strip, keyval.split("=", 1))
                  for keyval in re.split(r'(?<!\\);', auth_data)
                  if keyval.count("=") > 0 ]
    except Exception as err:
        Log.instance.message("auth_data.invalid",
                LogLevel.WARNING, LogContext.NO_CONTEXT,
                "Failed to parse --auth-data string: " + str(err))
        sys.exit(1)

    if not pairs:
        return None

    return dict(pairs)

def parse_command_line():
    """Parse command line options."""

    parser = PaludisOptionParser()
    parser.usage = usage.replace("<pkgname>", "<pkgname>...")

    parser.add_default_format_options()

    agroup = OptionGroup(parser, "Authentication Options")
    agroup.add_option("-a", "--auth-data", metavar = "STRING", dest =
        "auth_data",
        help = "Semicolon-separated key=value pairs for remote authentication")
    parser.add_option_group(agroup)

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
    proc, outfd = setup_pager()
    auth_data = parse_auth_data(options.auth_data)

    if proc is not None and options.colour:
        global NORM, PINK, GREEN, RED, BROWN, YELLOW
    else:
        NORM = PINK = GREEN = RED = BROWN = YELLOW = ""

    for package in args:
        for name, version, mkey in get_ids(env, package, options.include_masked):
            for value in mkey:
                try:
                    remote, id = str(value).split(":", 1)
                except ValueError:
                    Log.instance.message("remote.invalid", LogLevel.WARNING,
                            LogContext.NO_CONTEXT,
                            "Invalid REMOTE_IDS key `%s' in package %s-%s" %
                            (str(value), name, version))
                    continue
                handler = get_handler(remote)
                if handler is None:
                    Log.instance.message("remote.no_handler", LogLevel.WARNING,
                            LogContext.NO_CONTEXT,
                            "No handler for remote '%s'" % remote)
                    continue

                version_new = handler(id, auth_data=auth_data)
                if version_new is None:
                    continue
                elif version_new > version:
                    print(PINK + "N" + NORM, end=' ', file=outfd)
                    print("%s-{%s%s < %s%s} %s%s%s" % (name, PINK, version,
                            version_new, NORM, BROWN, value, NORM), file=outfd)
                elif version_new == version:
                    print(GREEN + "E" + NORM, end=' ', file=outfd)
                    print("%s-{%s%s = %s%s} %s%s%s" % (name, GREEN, version,
                            version_new, NORM, BROWN, value, NORM), file=outfd)
                else:
                    print(RED + "O" + NORM, end=' ')
                    print("%s-{%s%s > %s%s} %s%s%s" % (name, RED, version,
                            version_new, NORM, BROWN, value, NORM), file=outfd)

    if proc is not None:
        outfd.close()
        return proc.wait()

if __name__ == '__main__':
    main()
