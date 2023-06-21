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
__date__ = "10/02/2023"
__status__ = "stable"
__docformat__ = 'restructuredtext'

import logging
_logger = logging.getLogger(__name__)

from . import fabioimage
from .fabioutils import OrderedDict

try:
    import importlib
    importer = importlib.import_module
except ImportError:

    def importer(module_name):
        module = __import__(module_name)
        # returns the leaf module, instead of the root module
        names = module_name.split(".")
        names.pop(0)
        for name in names:
            module = getattr(module, name)
        return module

_default_codecs = [
    ("edfimage", "EdfImage"),
    ("dtrekimage", "DtrekImage"),
    ("tifimage", "TifImage"),
    ("marccdimage", "MarccdImage"),
    ("mar345image", "Mar345Image"),
    ("fit2dmaskimage", "Fit2dMaskImage"),
    ("brukerimage", "BrukerImage"),
    ("bruker100image", "Bruker100Image"),
    ("pnmimage", "PnmImage"),
    ("GEimage", "GeImage"),
    ("OXDimage", "OxdImage"),
    ("dm3image", "Dm3Image"),
    ("HiPiCimage", "HipicImage"),
    ("pilatusimage", "PilatusImage"),
    ("fit2dspreadsheetimage", "Fit2dSpreadsheetImage"),
    ("kcdimage", "KcdImage"),
    ("cbfimage", "CbfImage"),
    ("xsdimage", "XsdImage"),
    ("binaryimage", "BinaryImage"),
    ("pixiimage", "PixiImage"),
    ("raxisimage", "RaxisImage"),
    ("numpyimage", "NumpyImage"),
    ("eigerimage", "EigerImage"),
    ("hdf5image", "Hdf5Image"),
    ("fit2dimage", "Fit2dImage"),
    ("speimage", "SpeImage"),
    ("jpegimage", "JpegImage"),
    ("jpeg2kimage", "Jpeg2KImage"),
    ("mpaimage", "MpaImage"),
    ("mrcimage", "MrcImage"),
    ("esperantoimage", "EsperantoImage"),
    ("limaimage", "LimaImage"),
    # For compatibility (maybe not needed)
    ("adscimage", "AdscImage"),
    ("sparseimage", "SparseImage"),
    ("xcaliburimage", "XcaliburImage"),
]
"""List of relative module and class names for available formats in fabio.
Order matter."""

_registry = OrderedDict()
"""Contains all registered codec classes indexed by codec name."""

_extension_cache = None
"""Cache extension mapping"""


def register(codec_class):
    """Register a class format to the core fabio library"""
    global _extension_cache
    if not issubclass(codec_class, fabioimage.FabioImage):
        raise AssertionError("Expected subclass of FabioImage class but found %s" % type(codec_class))
    _registry[codec_class.codec_name()] = codec_class
    # clean u[p the cache
    _extension_cache = None


def register_default_formats():
    """Register all available default image classes provided by fabio.

    If a format is already registered, it will be overwriten
    """
    # we use __init__ rather than __new__ here because we want
    # to modify attributes of the class *after* they have been
    # created
    for module_name, class_name in _default_codecs:
        module = importer("fabio." + module_name)
        codec_class = getattr(module, class_name)
        if codec_class is None:
            raise RuntimeError("Class name '%s' from mudule '%s' not found" % (class_name, module_name))
        register(codec_class)


def get_all_classes():
    """Returns the list of supported codec identified by there fabio classes.

    :rtype: list"""
    return _registry.values()


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
    if format_name in _registry:
        return _registry[format_name]
    else:
        return None


def _get_extension_mapping():
    """Returns a dictionary mapping file extension to the list of supported
    formats. The result is cached, do not edit it

    :rtype: dict
    """
    global _extension_cache
    if _extension_cache is None:
        _extension_cache = {}
        for codec in get_all_classes():
            if not hasattr(codec, "DEFAULT_EXTENSIONS"):
                continue
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


def factory(name):
    """Factory of image using name of the codec class.

    :param str name: name of the class to instantiate
    :return: an instance of the class
    :rtype: fabio.fabioimage.FabioImage
    """
    name = name.lower()
    obj = None
    if name in _registry:
        obj = _registry[name]()
    else:
        msg = ("FileType %s is unknown !, "
               "please check if the filename exists or select one from %s" % (name, _registry.keys()))
        _logger.debug(msg)
        raise RuntimeError(msg)
    return obj
