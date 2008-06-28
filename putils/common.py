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

"""Common functions used by applets
"""

import inspect
import os
import sys

__all__ = [ "cache_return", "exiting_signal_handler" ]

class cache_return:
    """Decorator to cache the return values of a function."""
    def __init__(self, function):
        self.function = function
        # Use two lists instead of a dictionary
        # so unhashable objects can be cached as well.
        self.cache_args = []
        self.cache_rets = []

    def __call__(self, *args, **kwargs):
        if (args,kwargs) in self.cache_args:
            return self.cache_rets[self.cache_args.index((args,kwargs))]
        else:
            ret = self.function(*args, **kwargs)

            self.cache_args.append((args,kwargs))
            self.cache_rets.append(ret)

            return ret

def _get_module_name(path):
    """Get module name"""
    module_name = None
    for p in sys.path:
        if p and path.startswith(p):
            if not p.endswith(os.path.sep):
                p += os.path.sep
            path = path.replace(p, "")
            basename = os.path.basename(path)

            module_name = path.replace(basename,
                    inspect.getmodulename(basename))
            module_name = module_name.replace(os.path.sep, ".")
    return module_name

def exiting_signal_handler(signum, frame):
    """Signal handler that prints the signal and exits."""
    print >>sys.stderr, "\nCaught signal", signum,
    if frame.f_code.co_name is not None:
        module_name = _get_module_name(frame.f_code.co_filename)
        print >>sys.stderr, "in %s()" % ".".join((module_name,
                frame.f_code.co_name))
    else:
        print
    print >>sys.stderr, "\nExiting with failure"
    sys.exit(1)
