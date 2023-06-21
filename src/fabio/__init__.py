# coding: utf-8
#
#    Project: X-ray image reader
#             https://github.com/silx-kit/fabio
#
#
#    Copyright (C) European Synchrotron Radiation Facility, Grenoble, France
#
#    Principal author:       Jérôme Kieffer (Jerome.Kieffer@ESRF.eu)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""FabIO module"""

__author__ = "Jérôme Kieffer"
__contact__ = "Jerome.Kieffer@ESRF.eu"
__license__ = "GPLv3+"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__date__ = "21/06/2023"
__status__ = "stable"

import sys
import logging

if "ps1" in dir(sys):
    # configure logging with interactive console
    logging.basicConfig()

import os
from ._version import __date__ as date  # noqa
from ._version import version, version_info, hexversion, strictversion  # noqa
from . import fabioformats as _fabioformats

# provide a global fabio API
factory = _fabioformats.factory

# feed the library with all the available formats
_fabioformats.register_default_formats()

from . import fabioimage
from . import openimage

from .fabioutils import COMPRESSORS, jump_filename, FilenameObject, \
    previous_filename, next_filename, deconstruct_filename, \
    extract_filenumber, getnum, construct_filename, exists

# Compatibility with outside world:
filename_object = FilenameObject

from .openimage import openimage as open
from .openimage import open_series as open_series
from .openimage import openheader as openheader


def register(codec_class):
    """
    Register a codec class with the set of formats supported by fabio.

    It is a transitional function to prepare the next comming version of fabio.

    - On the current fabio library, when a module is imported, all the formats
        inheriting FabioImage are automatically registred. And this function is
        doing nothing.
    - On the next fabio library. Importing a module containing classes
        inheriting FabioImage will not be registered. And this function will
        register the class.

    The following source code will then provide the same behaviour on both
    fabio versions, and it is recommended to use it.

    .. code-block:: python

        @fabio.register
        class MyCodec(fabio.fabioimage.FabioImage):
            pass
    """
    assert(issubclass(codec_class, fabioimage.FabioImage))
    _fabioformats.register(codec_class)
    return codec_class


def tests():
    """
    Run the FabIO test suite.

    If the test-images are not already installed (via the debian package for example),
    they need to be downloaded from sourceforge.net, which make take a while.
    Ensure your network connection is operational and your proxy settings are correct,
    for example:

    export http_proxy=http://proxy.site.com:3128
    """
    from . import test
    test.run_tests()


def benchmarks():
    """
    Run the benchmarks
    """
    from . import benchmark
    res = benchmark.run()
    return res
