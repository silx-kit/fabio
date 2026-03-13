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
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#  .
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#  .
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.

"""FabIO module"""

__author__ = "Jérôme Kieffer"
__contact__ = "Jerome.Kieffer@ESRF.eu"
__license__ = "GPLv3+"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__date__ = "13/03/2026"
__status__ = "stable"

import sys
import logging
from .version import __date__ as date, version, version_info, hexversion, strictversion  # noqa
from . import fabioformats as _fabioformats
from . import fabioimage  # noqa
from . import openimage  # noqa
from .fabioutils import (
    jump_filename,  # noqa
    FilenameObject,  # noqa
    previous_filename,  # noqa
    next_filename,  # noqa
    deconstruct_filename,  # noqa
    extract_filenumber,  # noqa
    getnum,  # noqa
    construct_filename,  # noqa
    exists,  # noqa
)  # noqa
from .compression import COMPRESSORS  # noqa
from .openimage import openimage as open  # noqa
from .openimage import open_series as open_series  # noqa
from .openimage import openheader as openheader  # noqa

if "ps1" in dir(sys):
    # configure logging with interactive console
    logging.basicConfig()

# provide a global fabio API
factory = _fabioformats.factory

# feed the library with all the available formats
_fabioformats.register_default_formats()

# Compatibility with outside world:
filename_object = FilenameObject


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
    assert issubclass(codec_class, fabioimage.FabioImage)
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
