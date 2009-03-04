#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set sw=4 ts=4 sts=4 et tw=80 :
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

"""Common utilities
"""

__all__ = [ "rootjoin", ]

import os

def rootjoin(path, root):
    """Smartly join path and root so there's no more than one / between them."""
    if root == os.path.sep:
        return path

    if root.endswith(os.path.sep):
        if path.startswith(os.path.sep):
            return root[:-1] + path
        else:
            return root + path

    if path.startswith(os.path.sep):
        return root + path
    else:
        return root + os.path.sep + path
