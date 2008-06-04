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

"""paludis-utils setup
"""

import os
import sys

from distutils import log
from distutils.core import setup
from distutils.command.install_scripts import install_scripts

sys.path.insert(0, os.path.realpath(os.path.abspath(__file__)))
import putils
import putils.applets

applets = putils.applets.__all__
VIRTUAL_APPLET = "p"

class symlinking_install_scripts(install_scripts, object):

    def run(self):
        super(symlinking_install_scripts, self).run()

        global applets, VIRTUAL_APPLET

        log.info("Creating symlinks")

        build_dir = os.getcwd()
        os.chdir(self.install_dir)
        for applet in applets:
            log.info(applet + " -> " + VIRTUAL_APPLET)
            # Check for existing symlinks
            if os.path.islink(applet):
                if os.path.basename(os.path.realpath(applet)) == VIRTUAL_APPLET:
                    # Symlink points to where we want.
                    continue
                else:
                    os.unlink(applet)
            os.symlink(VIRTUAL_APPLET, applet)

        os.chdir(build_dir)

setup(name = putils.__name__,
        version = putils.__version__,
        license = putils.__license__,
        description = "Useful utilities for paludis",
        author = putils.__author__.split("<")[0].strip(),
        author_email = putils.__author__.split("<")[1].strip(">"),
        url = "http://hawking.nonlogic.org/projects/paludis-utils",
        packages = [ "putils", "putils/applets" ],
        scripts = [ "scripts/" + VIRTUAL_APPLET, ],
        cmdclass = { "install_scripts" : symlinking_install_scripts }
        )
