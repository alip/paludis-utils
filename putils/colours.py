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

"""Colourify filenames using LS_COLORS
There are some differences to ls(1)'s behaviour.
For performance reasons we first check wildcards before stat()'ing the file and
checking whether it's setuid, setgid, executable etc.
"""

import os
import fnmatch
import re

from stat import S_IMODE

from paludis import (ContentsDevEntry, ContentsDirEntry, ContentsFifoEntry,
        ContentsFileEntry, ContentsSymEntry, ContentsMiscEntry)

from putils.common import cache_return

__all__ = [ "colourify_content" , "no_colourify_content" ]

# Special keys in LS_COLORS
lscolours_keys = ( "tw", "ow", "st", "su", "sg", "or", "ln", "pi", "so", "do",
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

        if key in lscolours_keys:
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

def colourify_file(filename, colour_codes, special_codes, root=""):
    """Colourify given filename."""
    wildcard_regex = translate(colour_codes)
    match = wildcard_regex.match(filename)

    if match is not None:
        # The first matched group is the parent, skip it.
        key_index = list(match.groups()[1:]).index(filename)
        key = colour_codes.keys()[key_index]

        return "\033[" + colour_codes[key] + "m" + root + filename + "\033[m"
    else:
        # Only stat() files here.
        # TODO users should be able to customize the behaviour and avoid this stat()
        try:
            mode = os.stat(filename)[0]
        except OSError, e:
            if e.errno == 2: # File doesn't exist
                return "\033[" + special_codes.get("mi", "00") + "m" + root + filename + "\033[m"
            elif e.errno == 13: # Not allowed to stat()
                return "\033[7m" + root + filename + "\033[m"
        else:
            if S_IMODE(mode) & 04000: # File is setuid (u+s)
                return "\033[" + special_codes.get("su", "00") + "m" + root + filename + "\033[m"
            elif S_IMODE(mode) & 02000: # File is setgid (g+s)
                return "\033[" + special_codes.get("sg", "00") + "m" + root + filename + "\033[m"
            elif os.access(filename, os.X_OK): # File is executable
                return "\033[" + special_codes.get("ex", "00") + "m" + root + filename + "\033[m"
            else:
                return root + filename

def colourify_content(content, root="", target=False):
    """Colourify content name using LS_COLORS.
    If target is True and content is a symbolic link,
    colourify content.target instead of content.name."""

    codes, special_codes = parse_ls_colours()
    if not codes and not special_codes:
        return content.name

    if root:
        root += os.path.sep

    if isinstance(content, ContentsDevEntry):
        return "\033[" + special_codes.get("bd", "00") + "m" + root + content.name + "\033[m"
    elif isinstance(content, ContentsDirEntry):
        return "\033[" + special_codes.get("di", "00") + "m" + root + content.name + "\033[m"
    elif isinstance(content, ContentsFifoEntry):
        return "\033[" + special_codes.get("pi", "00") + "m" + root + content.name + "\033[m"
    elif isinstance(content, ContentsFileEntry):
        return colourify_file(content.name, codes, special_codes, root)
    elif isinstance(content, ContentsSymEntry):
        if not target:
            return "\033[" + special_codes.get("ln", "00") + "m" + root + content.name + "\033[m"
        elif os.path.isabs(content.target):
            return colourify_file(content.target, codes, special_codes, root)
        else:
            dname = os.path.dirname(content.name)
            abstarget = os.path.join(dname, content.target)
            return colourify_file(abstarget, codes, special_codes, root).replace(
                        dname + os.path.sep, '')
    else:
        return root + content.name

def no_colourify_content(content, root="", target=False):
    """Dummy replacement for colourify_content() with no colouring."""
    if root: root += os.path.sep
    if target: return root + content.target
    else: return root + content.name
