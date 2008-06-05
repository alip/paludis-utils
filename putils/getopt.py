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

"""Option parsing for paludis clients.
"""

import os
import sys
import optparse
import re
import textwrap

from paludis import (Log, LogLevel, LogContext, VERSION_MAJOR, VERSION_MINOR,
        VERSION_MICRO, VERSION_SUFFIX, SUBVERSION_REVISION)

__all__ = [ "PaludisOptionParser", "version" ]

# Don't seperate hyphenated words
textwrap.TextWrapper.wordsep_re = re.compile(
        r'(\s+|'                                  # any whitespace
#    r'[^\s\w]*\w+[a-zA-Z]-(?=\w+[a-zA-Z])|'   # hyphenated words
        r'(?<=[\w\!\"\'\&\.\,\?])-{2,}(?=\w))')   # em-dash

def version():
    """Return version details"""
    from putils import __name__, __version__, __copyright__
    from paludis import (VERSION_MAJOR, VERSION_MINOR, VERSION_MICRO,
            VERSION_SUFFIX, SUBVERSION_REVISION)

    version_str = __name__ + " "  + __version__ + ", "
    version_str += "using paludis " + str(VERSION_MAJOR) + "." +\
            str(VERSION_MINOR) + "." + str(VERSION_MAJOR) +\
            VERSION_SUFFIX

    if SUBVERSION_REVISION:
        version_str += " r" + SUBVERSION_REVISION
    version_str += "\n\n"

    version_str += "\n".join(textwrap.wrap(__copyright__))

    return version_str

class PaludisOptionParser(optparse.OptionParser, object):
    """OptionParser specialized for Paludis."""

    __options_query = False
    __options_advanced_query = False
    __options_content_limit = False

    def __init__(self,
                 usage=None,
                 option_list=None,
                 option_class=optparse.Option,
                 version=None,
                 conflict_handler="error",
                 description=None,
                 formatter=None,
                 add_help_option=True,
                 prog=None,
                 epilog=None):
        super(PaludisOptionParser, self).__init__(usage, option_list,
                option_class, version, conflict_handler, description,
                formatter, add_help_option, prog, epilog)

        # Add --version option
        self.add_option("-V", "--version", action = "callback",
                callback = self.cb_version,
                help = "Display program version")
        # Add common paludis options
        self.add_option("-E", "--environment", action = "store",
            dest = "environment", default = "",
            help = "Environment specification")
        self.add_option("", "--log-level", type = "choice",
            choices = ["debug", "qa", "warning", "silent"],
            action = "store", dest = "log_level",
            help = "Specify the log level")

        # Respect %PROG_OPTION environment variable
        environment_variable = self.get_prog_name().upper() + "_OPTIONS"
        if environment_variable in os.environ:
            sys.argv += os.environ[environment_variable].split(" ")
        self.epilog = " ".join((environment_variable,
            "can be set for default command-line options."))

    def parse_args(self, args=None, values=None):
        (options, args) = super(PaludisOptionParser, self).parse_args(args, values)

        Log.instance.program_name = self.get_prog_name()

        # Set log level
        if options.log_level:
            Log.instance.log_level = getattr(LogLevel,
                    options.log_level.upper())

        # Check conflicting options
        if self.__options_advanced_query:
            if (options.ignore_case and options.regexp is None and
                    options.fnpattern is None):
                Log.instance.message("cmdline.option_not_valid",
                        LogLevel.WARNING, LogContext.NO_CONTEXT,
                        "Option --ignore-case is only valid with --regexp and/or --fnmatch options")

        return (options, args)

    def add_default_query_options(self, title="Query Options"):
        """Add default query options."""

        if not self.__options_query:
            option_group_query = optparse.OptionGroup(self, title)

            help_selection = """Specify selection. One of:
all-versions-grouped-by-slot, all-versions-sorted, all-versions-unsorted,
best-version-in-each-slot, require-exactly-one, some-arbitrary-version
    Default: %default"""

            option_group_query.add_option("-S", "--selection", type = "choice",
                    choices = ["all-versions-grouped-by-slot", "all-versions-sorted",
                        "all-versions-unsorted", "best-version-in-each-slot",
                        "require-exactly-one", "some-arbitrary-version" ],
                    action = "store", dest = "selection",
                    default = "all-versions-grouped-by-slot", help = help_selection )
            self.add_option_group(option_group_query)
        self.__options_query = True

    def add_default_advanced_query_options(self,
        title="Advanced Query Options"):
        """Add default advanced query options."""

        if not self.__options_advanced_query:
            option_group_aquery = optparse.OptionGroup(self, title)

            option_group_aquery.add_option("-e", "--regexp", dest = "regexp",
                    metavar = "PATTERN", help = "List files matching PATTERN")
            option_group_aquery.add_option("-n", "--fnmatch", dest = "fnpattern",
                    metavar = "PATTERN",
                    help = "List files matching PATTERN using Unix shell-style wildcards")
            option_group_aquery.add_option("-i", "--ignore-case", action = "store_true",
                    dest = "ignore_case", help = "Ignore case distinctions in PATTERN")
            self.add_option_group(option_group_aquery)

        self.__options_advanced_query = True

    def add_default_content_limit_options(self,
            title="Limiting by type of content"):
        """Add default limit options."""

        if not self.__options_content_limit:
            option_group_climit = optparse.OptionGroup(self, title)

            option_group_climit.add_option("-d", "--dir", action = "store_true",
                    dest = "only_directories", default = False,
                    help = "Only directories")
            option_group_climit.add_option("-f", "--file", action = "store_true",
                    dest = "only_files", default = False,
                    help = "Only files")
            option_group_climit.add_option("-m", "--misc", action = "store_true",
                    dest = "only_misc", default = False,
                    help = "Only misc entries")
            option_group_climit.add_option("-s", "--symlink", action = "store_true",
                    dest = "only_symlink", default = False,
                    help = "Only symlinks")
            option_group_climit.add_option("-D", "--device", action = "store_true",
                    dest = "only_dev", default = False,
                    help = "Only devices")
            option_group_climit.add_option("-F", "--fifo", action = "store_true",
                    dest = "only_fifo", default = False,
                    help = "Only fifos")
            self.add_option_group(option_group_climit)
        self.__options_content_limit = True

    # Option callbacks
    def cb_version(self, option, opt_str, value, parser):
        """Callback for --version"""
        version_str = self.get_prog_name() + ", part of " + version()

        print version_str
        sys.exit(0)
