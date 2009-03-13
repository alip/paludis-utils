#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 sts=4 et tw=80 fdm=indent :
#
# Copyright (c) 2008 Ali Polatel <polatel@gmail.com>
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

"""Hook to allow user-specified customization code to run.
"""

# Based on user module from stdlib

import os

home = os.curdir
if "HOME" in os.environ:
    home = os.environ["HOME"]
elif os.name == "posix":
    home = os.path.expanduser("~/")

putils_rc = os.path.join(home, ".p/putils_conf.py")
try:
    f = open(putils_rc)
except IOError:
    pass
else:
    f.close()
    try:
        execfile(putils_rc)
    except Exception, e:
        from paludis import Log, LogContext, LogLevel
        Log.instance.message("user_file.invalid", LogLevel.WARNING,
                LogContext.NO_CONTEXT,
                "User customization file constains error: %s" % e.message)
