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

    options, args = parser.parse_args()

    return options, args
#}}}

def main(): #{{{
    options, args = parse_command_line()
    env = EnvironmentMaker.instance.make_from_spec(options.environment)

    for filename in args:
        content_generator = search_contents(filename, env)

        for package_id, content in content_generator:
            print package_id, "(" + content.name + ")"
#}}}

if __name__ == '__main__':
    main()

