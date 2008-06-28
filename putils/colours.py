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

"""Colorify filenames using LS_COLORS
"""

import os
import fnmatch
import re

from stat import *

from putils.common import cache_return

__all__ = [ "colourify_file" ]

# Special keys in LS_COLORS
# The lambda functions are only called if the file exists!
special_keys = {
        # Normal
        "no" : lambda f, mode: True,
        # File
        "fi" : lambda f, mode: S_ISREG(mode),
        # Directory
        "di" : lambda f, mode: S_ISDIR(mode),
        # Symbolic link
        "ln" : lambda f, mode: os.path.islink(f),
        # Fifo
        "pi" : lambda f, mode: S_ISFIFO(mode),
        # Socket
        "so" : lambda f, mode: S_ISSOCK(mode),
        # Door FIXME
        "do" : lambda f, mode: False,
        # Block device driver
        "bd" : lambda f, mode: S_ISBLK(mode),
        # Character device driver
        "cd" : lambda f, mode: S_ISCHR(mode),
        # Orphaned symlinks
        "or" : lambda f, mode: (os.path.islink(f) and
                            not os.path.exists(os.path.realpath(f))),
        # Missing files
        "mi" : lambda f, mode: False,
        # File that is setuid (u+s)
        "su" : lambda f, mode: (S_ISREG(mode) and
                            S_IMODE(mode) & 04000),
        # File that is setgid (g+s)
        "sg" : lambda f, mode: (S_ISREG(mode) and
                            S_IMODE(mode) & 02000),
        # Dir that is sticky and other-writable (+t,o+w)
        "tw" : lambda f, mode: (S_ISDIR(mode) and
                            S_IMODE(mode) & 01000 and
                            S_IMODE(mode) & 0002 ),
        # Dir that is other-writable (o+w) and not sticky
        "ow" : lambda f, mode: (S_ISDIR(mode) and
                            S_IMODE(mode) & 0002 and
                            S_IMODE(mode) & 01000 == 0),
        # Dir that is sticky and not other-writable
        "st" : lambda f, mode: (S_ISDIR(mode) and
                            S_IMODE(mode) & 01000 and
                            S_IMODE(mode) & 0002 == 0),
        # Executable
        "ex" : lambda f, mode: S_ISREG(mode) and os.access(f, os.X_OK),
}
# The order in which we should check them,
# From most specific to least specific
special_keys_sorted = ( "tw", "ow", "st", "su", "sg", "or", "ln", "pi", "so", "do",
        "bd", "cd", "di", "ex", "fi", "mi", "no" )

@cache_return
def parse_ls_colours(): #{{{
    """Convert LS_COLORS into two dictionaries,
    One has wildcards and associated colour codes,
    the other has special codes and associated colour codes,"""

    if not "LS_COLORS" in os.environ:
        return None, None

    codes = dict()
    special_codes = dict()
    for equation in os.environ["LS_COLORS"].split(":"):
        if not "=" in equation:
            continue

        key, colour_code = equation.split("=")

        if key in special_keys_sorted:
            special_codes[key] = colour_code
        else:
            codes[key] = colour_code

    return codes, special_codes
#}}}

@cache_return
def translate(wildcards, flags=0): #{{{
    """Translate a group of wildcards into a compiled regex"""
    regex = "("

    index = 0
    last_index = len(wildcards) - 1
    for wildcard in wildcards:
        regex += "(" + fnmatch.translate(wildcard) + ")"
        if last_index != index:
            regex += "|"
        index += 1

    regex += ")"

    return re.compile(regex, flags)
#}}}

def colourify_file(filename): #{{{
    """Colourify filename as ls would using LS_COLORS."""
    codes, special_codes = parse_ls_colours()
    if not codes and not special_codes:
        return filename

    wildcard_regex = translate(codes)

    try:
        mode = os.stat(filename)[0]
    except OSError, e:
        if e.errno == 2: # File doesn't exist
            missing = True
        elif e.errno == 13: # Not allowed to stat()
            missing = False
        mode = False

    if mode:
        match = wildcard_regex.match(filename)
        if match is not None:
            # The first matched group is the parent, skip it.
            key_index = list(match.groups()[1:]).index(filename)
            key = codes.keys()[key_index]

            return "\033[" + codes[key] + "m" + filename + "\033[m"

        for key in special_keys_sorted:
            if special_keys[key](filename, mode):
                return "\033[" + special_codes[key] + "m" + filename + "\033[m"
    elif missing:
        # File is missing -- "mi"
        return "\033[" + special_codes["mi"] + "m" + filename + "\033[m"
    else:
        # Permission denied
        return "\033[7m" + filename + "\033[m"

    return filename
#}}}
