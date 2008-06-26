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

from stat import *

__all__ = [ "colourify_file" ]

# Special keys in LS_COLORS
special_keys = {
        # Normal
        "no" : lambda f: os.path.exists(f),
        # File
        "fi" : lambda f: os.path.isfile(f),
        # Directory
        "di" : lambda f: os.path.isdir(f),
        # Symbolic link
        "ln" : lambda f: os.path.islink(f),
        # Fifo
        "pi" : lambda f: os.path.exists(f) and S_ISFIFO(os.stat(f)[0]),
        # Socket
        "so" : lambda f: os.path.exists(f) and S_ISSOCK(os.stat(f)[0]),
        # Door FIXME
        "do" : lambda f: False,
        # Block device driver
        "bd" : lambda f: os.path.exists(f) and S_ISBLK(os.stat(f)[0]),
        # Character device driver
        "cd" : lambda f: os.path.exists(f) and S_ISCHR(os.stat(f)[0]),
        # Orphaned symlinks
        "or" : lambda f: (os.path.islink(f) and
                            not os.path.exists(os.path.realpath(f))),
        # Missing files
        "mi" : lambda f: not os.path.exists(f),
        # File that is setuid (u+s)
        "su" : lambda f: (os.path.isfile(f) and
                            S_IMODE(os.stat(f)[0]) & 04000),
        # File that is setgid (g+s)
        "sg" : lambda f: (os.path.isfile(f) and
                            S_IMODE(os.stat(f)[0]) & 02000),
        # Dir that is sticky and other-writable (+t,o+w)
        "tw" : lambda f: (os.path.isdir(f) and
                            S_IMODE(os.stat(f)[0]) & 01000 and
                            S_IMODE(os.stat(f)[0]) & 0002 ),
        # Dir that is other-writable (o+w) and not sticky
        "ow" : lambda f: (os.path.isdir(f) and
                            S_IMODE(os.stat(f)[0]) & 0002 and
                            S_IMODE(os.stat(f)[0]) & 01000 == 0),
        # Executable
        "ex" : lambda f: os.path.isfile(f) and os.access(f, os.X_OK),
}
# The order in which we should check them,
# From most specific to least specific
special_keys_sorted = ( "tw", "ow", "su", "sg", "or", "ln", "pi", "so", "do",
        "bd", "cd", "di", "ex", "fi", "mi", "no" )

def grab_colours():
    """Convert LS_COLORS into two dictionaries,
    One has wildcards and associated colour codes,
    the other has special codes and associated colour codes,"""

    if not "LS_COLORS" in os.environ:
        return None, None

    codes = special_codes = dict()
    for equation in os.environ["LS_COLORS"].split(":"):
        if not "=" in equation:
            continue

        key, colour_code = equation.split("=")

        if key in special_keys_sorted:
            special_codes[key] = colour_code
        else:
            codes[key] = colour_code

    return codes, special_codes

_colour_codes_cache = None
_colour_special_codes_cache = None
def colourify_file(filename): #{{{
    """Colourify filename as ls would using LS_COLORS."""
    global _colour_codes_cache, _colour_special_codes_cache
    if _colour_codes_cache is None and _colour_special_codes_cache is None:
        codes, special_codes = grab_colours()

        if not codes and not special_codes:
            return filename

        _colour_codes_cache = codes
        _colour_special_codes_cache = special_codes
    else:
        codes = _colour_codes_cache
        special_codes = _colour_special_codes_cache

    if os.path.exists(filename):
        for key in codes:
            if fnmatch.fnmatch(filename, key):
                return "\033[" + codes[key] + "m" + filename + "\033[m"

    for key in special_keys_sorted:
        if special_keys[key](filename):
            return "\033[" + special_codes[key] + "m" + filename + "\033[m"

    return filename
#}}}

