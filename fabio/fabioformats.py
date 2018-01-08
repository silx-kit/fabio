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
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE

"""
Provide an API to all the supported formats
"""

__author__ = "Valentin Valls"
__contact__ = "valentin.valls@esrf.eu"
__license__ = "MIT"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__date__ = "27/07/2017"
__status__ = "stable"
__docformat__ = 'restructuredtext'

import logging
_logger = logging.getLogger(__name__)

from . import fabioimage

# Note: The order of the import is important for the import sequence
from . import edfimage  # noqa
from . import adscimage  # noqa
from . import tifimage  # noqa
from . import marccdimage  # noqa
from . import mar345image  # noqa
from . import fit2dmaskimage  # noqa
from . import brukerimage  # noqa
from . import bruker100image  # noqa
from . import pnmimage  # noqa
from . import GEimage  # noqa
from . import OXDimage  # noqa
from . import dm3image  # noqa
from . import HiPiCimage  # noqa
from . import pilatusimage  # noqa
from . import fit2dspreadsheetimage  # noqa
from . import kcdimage  # noqa
from . import cbfimage  # noqa
from . import xsdimage  # noqa
from . import binaryimage  # noqa
from . import pixiimage  # noqa
from . import raxisimage  # noqa
from . import numpyimage  # noqa
from . import eigerimage  # noqa
from . import hdf5image  # noqa
from . import fit2dimage  # noqa
from . import speimage  # noqa
from . import jpegimage  # noqa
from . import jpeg2kimage  # noqa
from . import mpaimage  # noqa


def get_all_classes():
    """Returns the list of supported codec identified by there fabio classes.

    :rtype: list"""
    return fabioimage.FabioImage.registry.values()


def get_classes(reader=None, writer=None):
    """
    Return available codecs according to filter

    :param bool reader: True to reach codecs providing reader or False to
        provide codecs which do not provided reader. If None, reader feature is
        not filtered
    :param bool writer: True to reach codecs providing writer or False to
        provide codecs which do not provided writer. If None, writer feature is
        not filtered
    :rtype: list
    """
    formats = []
    for f in get_all_classes():
        # assert that if the read is redefined, then there is a reader
        has_reader = f.read.__module__ != fabioimage.__name__
        # assert that if the write is redefined, then there is a writer
        has_writer = f.write.__module__ != fabioimage.__name__

        include_format = True
        if reader is not None and reader != has_reader:
            include_format = False
        if writer is not None and writer != has_writer:
            include_format = False
        if include_format:
            formats.append(f)
    return formats


def get_class_by_name(format_name):
    """
    Get a format class by its name.

    :param str format_name: Format name, for example, "edfimage"
    :return: instance of the new class
    """
    if format_name in fabioimage.FabioImage.registry:
        return fabioimage.FabioImage.registry[format_name]
    else:
        return None


_extension_cache = None
"""Cache extension mapping"""


def _get_extension_mapping():
    """Returns a dictionary mapping file extension to the list of supported
    formats. The result is cached, do not edit it

    :rtype: dict
    """
    global _extension_cache
    if _extension_cache is None:
        _extension_cache = {}
        for codec in get_all_classes():
            for ext in codec.DEFAULT_EXTENSIONS:
                if ext not in _extension_cache:
                    _extension_cache[ext] = []
                _extension_cache[ext].append(codec)
    return _extension_cache


def get_classes_from_extension(extension):
    """
    Returns list of supported file format classes from a file extension

    :param str extension: File extension, for example "edf"
    :return: fabio image class
    """
    mapping = _get_extension_mapping()
    extension = extension.lower()
    if extension in mapping:
        # clone the list
        return list(mapping[extension])
    else:
        return []


def is_extension_supported(extension):
    """
    Returns true is the extension is supported.

    :param str format_name: Format name, for example, "edfimage"
    :return: instance of the new class
    """
    mapping = _get_extension_mapping()
    extension = extension.lower()
    return extension in mapping
