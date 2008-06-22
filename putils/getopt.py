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
import re
import textwrap
from copy import copy
from types import ListType, TupleType
from optparse import (Option, OptionGroup, OptionParser, AmbiguousOptionError,
        OptionError, OptionValueError)

from paludis import Log, LogLevel, LogContext, Selection

__all__ = [ "PaludisOptionParser", "SmartOption", "version" ]

# Don't seperate hyphenated words
textwrap.TextWrapper.wordsep_re = re.compile(
        r'(\s+|'                                  # any whitespace
#    r'[^\s\w]*\w+[a-zA-Z]-(?=\w+[a-zA-Z])|'   # hyphenated words
        r'(?<=[\w\!\"\'\&\.\,\?])-{2,}(?=\w))')   # em-dash

def version():
    """Return version details"""
    from putils import __name__, __version__, __copyright__
    from paludis import (GIT_HEAD, VERSION_MAJOR, VERSION_MINOR, VERSION_MICRO,
            VERSION_SUFFIX)

    version_str = __name__ + " "  + __version__ + ", "
    version_str += "using paludis " + str(VERSION_MAJOR) + "." +\
            str(VERSION_MINOR) + "." + str(VERSION_MAJOR) +\
            VERSION_SUFFIX

    if GIT_HEAD:
        version_str += GIT_HEAD
    version_str += "\n\n"

    version_str += "\n".join(textwrap.wrap(__copyright__))

    return version_str

def _regex_strip_name(regexp):
    """Strip the name part of the regex (?P<.*>)"""

    stripper = re.compile(r'(.*?)\(\?P<.*?>(.*)\)(.*)')
    stripped_regexp = stripper.sub(r'\1\2\3', regexp)

    return stripped_regexp

def check_regex_choice(option, opt, value):
    """Check regex_choice"""
    for regexp in option.choices:
        choice_re = re.compile(regexp, option.regex_flag)
        m = choice_re.match(value)
        if m is not None:
            real_value = m.groupdict().keys()[0]
            Log.instance.message("optparse.regex_choice.choosed",
                    LogLevel.DEBUG, LogContext.NO_CONTEXT,
                    "For option '%s' expanded '%s' to '%s'" % (opt, value, real_value))
            return real_value

    if (option.regex_flag & re.VERBOSE) == re.VERBOSE:
        strip_space = lambda string: re.sub("\s", "", string)
        option.choices = map(strip_space, option.choices)

    choices = ",\n".join(
            map(repr,
                map(_regex_strip_name, option.choices)))

    raise OptionValueError("""option %s: invalid choice: %r
Choice must match one of the following regexps:
%s""" % (opt, value, choices))

class SmartOption(Option):
    """Extend Option to add a new type regex_choice"""

    TYPES = Option.TYPES + ("regex_choice",)
    TYPE_CHECKER = copy(Option.TYPE_CHECKER)
    TYPE_CHECKER["regex_choice"] = check_regex_choice

    ATTRS = copy(Option.ATTRS)
    ATTRS.append("regex_flag")

    def _check_choice(self):
        """Extended for regex_choice"""
        if self.type and self.type.endswith("choice"):
            if self.choices is None:
                raise OptionError(
                    "must supply a list of choices for type 'choice'", self)
            elif type(self.choices) not in (TupleType, ListType):
                raise OptionError(
                    "choices must be a list of strings ('%s' supplied)"
                    % str(type(self.choices)).split("'")[1], self)
        elif self.choices is not None:
            raise OptionError(
                "must not supply choices for type %r" % self.type, self)

    CHECK_METHODS = copy(Option.CHECK_METHODS)
    for function in CHECK_METHODS:
        if function.func_name == "_check_choice":
            index = CHECK_METHODS.index(function)
            CHECK_METHODS.remove(function)
            CHECK_METHODS.insert(index, _check_choice)
            break

class PaludisOptionParser(OptionParser, object):
    """OptionParser specialized for Paludis."""

    __options_query = False
    __options_advanced_query = False
    __options_content_limit = False

    def __init__(self,
                 usage=None,
                 option_list=None,
                 option_class=SmartOption,
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

        # Selection
        if self.__options_query:
            options.selection = getattr(Selection, options.selection)

        # Check conflicting options
        if self.__options_advanced_query:
            if (options.ignore_case and options.regexp is None and
                    options.fnpattern is None):
                Log.instance.message("cmdline.option_not_valid",
                        LogLevel.WARNING, LogContext.NO_CONTEXT,
                        "Option --ignore-case is only valid with --regexp and/or --fnmatch options")

        # Requested instances
        if self.__options_content_limit:
            from paludis import (ContentsDevEntry, ContentsDirEntry,
                    ContentsFileEntry, ContentsFifoEntry, ContentsMiscEntry,
                    ContentsSymEntry)

            ri = []
            if options.list_Dev:
                ri.append(ContentsDevEntry)
            if options.list_Dir:
                ri.append(ContentsDirEntry)
            if options.list_Fifo:
                ri.append(ContentsFifoEntry)
            if options.list_File:
                ri.append(ContentsFileEntry)
            if options.list_Misc:
                ri.append(ContentsMiscEntry)
            if options.list_Sym:
                ri.append(ContentsSymEntry)
            if not ri:
                ri.append(object)
            options.requested_instances = ri

        return (options, args)

    def add_default_query_options(self, title="Query Options"):
        """Add default query options."""

        if not self.__options_query:
            option_group_query = OptionGroup(self, title)

            help_selection = """Specify selection. One of:
all-versions-grouped-by-slot, all-versions-sorted, all-versions-unsorted,
best-version-in-each-slot, best-version-only, require-exactly-one, some-arbitrary-version
                        Default: %default"""

            option_group_query.add_option("-S", "--selection", type = "regex_choice",
                    choices = [
"""^(?P<AllVersionsUnsorted>
avu|
(all-versions-u
    (n(s(o(r(t(e(d)?)?)?)?)?)?)?
))$
""",
"""^(?P<AllVersionsSorted>
avs|
(all-versions-s(o(r(t(e(d)?)?)?)?)?
))$
""",
"""^(?P<AllVersionsGroupedBySlot>
avgbs|
(a(l(l(-(v(e(r(s(i(o(n(s(-(g(r(o(u(p(e(d(-(b(y(-(s(l(o(t)?
    )?)?)?)?)?)?)?)?)?)?)?)?)?)?)?)?)?)?)?)?)?)?)?)?)?)?
))$""",
"""^(?P<BestVersionInEachSlot>
bvies|
(b(e(s(t(-(v(e(r(s(i(o(n(-(i(n(-(e(a(c(h(-(s(l(o(t)?
    )?)?)?)?)?)?)?)?)?)?)?)?)?)?)?)?)?)?)?)?)?)?)?
))$""",
"""^(?P<BestVersionOnly>
bvo|
(best-version-o(n(l(y)?)?)?
))$""",
"""^(?P<RequireExactlyOne>
reo|
(r(e(q(u(i(r(e(-(e(x(a(c(t(l(y(-(o(n(e)?
    )?)?)?)?)?)?)?)?)?)?)?)?)?)?)?)?)?
))$""",
"""^(?P<SomeArbitraryVersion>
sav|
(s(o(m(e(-(a(r(b(i(t(r(a(r(y(-(v(e(r(s(i(o(n)?
    )?)?)?)?)?)?)?)?)?)?)?)?)?)?)?)?)?)?)?)?
))$""" ],

                    regex_flag = re.VERBOSE,
                    action = "store", dest = "selection",
                    default = "all-versions-grouped-by-slot", help = help_selection )
            self.add_option_group(option_group_query)
        self.__options_query = True

    def add_default_advanced_query_options(self,
        title="Advanced Query Options"):
        """Add default advanced query options."""

        if not self.__options_advanced_query:
            option_group_aquery = OptionGroup(self, title)

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
            option_group_climit = OptionGroup(self, title)

            option_group_climit.add_option("-d", "--dir", action = "store_true",
                    dest = "list_Dir", default = False,
                    help = "List directories")
            option_group_climit.add_option("-f", "--file", action = "store_true",
                    dest = "list_File", default = False,
                    help = "List files")
            option_group_climit.add_option("-m", "--misc", action = "store_true",
                    dest = "list_Misc", default = False,
                    help = "List misc entries")
            option_group_climit.add_option("-s", "--symlink", action = "store_true",
                    dest = "list_Sym", default = False,
                    help = "List symlinks")
            option_group_climit.add_option("-D", "--device", action = "store_true",
                    dest = "list_Dev", default = False,
                    help = "List devices")
            option_group_climit.add_option("-F", "--fifo", action = "store_true",
                    dest = "list_Fifo", default = False,
                    help = "List fifos")
            self.add_option_group(option_group_climit)
        self.__options_content_limit = True

    # Option callbacks
    def cb_version(self, option, opt_str, value, parser):
        """Callback for --version"""
        version_str = self.get_prog_name() + ", part of " + version()

        print version_str
        sys.exit(0)
