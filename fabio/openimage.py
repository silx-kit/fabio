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

Authors: Henning O. Sorensen & Erik Knudsen
         Center for Fundamental Research: Metal Structures in Four Dimensions
         Risoe National Laboratory
         Frederiksborgvej 399
         DK-4000 Roskilde
         email:henning.sorensen@risoe.dk

mods for fabio by JPW
modification for HDF5 by Jérôme Kieffer

"""
# Get ready for python3:
from __future__ import with_statement, print_function, absolute_import

import sys
import logging
logger = logging.getLogger("openimage")
from .fabioutils import FilenameObject, exists, BytesIO, six
from .fabioimage import FabioImage
from . import edfimage
from . import adscimage
from . import tifimage
from . import marccdimage
from . import mar345image
from . import fit2dmaskimage
from . import brukerimage
from . import bruker100image
from . import pnmimage
from . import GEimage
from . import OXDimage
from . import dm3image
from . import HiPiCimage
from . import pilatusimage
from . import fit2dspreadsheetimage
from . import kcdimage
from . import cbfimage
from . import xsdimage
from . import binaryimage
from . import pixiimage
from . import hdf5image
from . import raxisimage
from . import numpyimage
from . import eigerimage
from . import fit2dimage
from . import speimage

if six.PY2:
    bytes = str
    from urlparse import urlparse
else:
    from urllib.parse import urlparse

MAGIC_NUMBERS = [
                 # "\42\5a" : 'bzipped'
                 # "\1f\8b" : 'gzipped'
                 (b"FORMAT :        86", 'bruker'),
                 (b"\x4d\x4d\x00\x2a", 'tif'),
                 # The marCCD and Pilatus formats are both standard tif with a header
                 # hopefully these byte patterns are unique for the formats
                 # If not the image will be read, but the is missing
                 (b"\x49\x49\x2a\x00\x08\x00", 'marccd/tif'),
                 (b"\x49\x49\x2a\x00\x82\x00", 'pilatus'),
                 (b"\x49\x49\x2a\x00", 'tif'),
                 # ADSC must come before edf
                 (b"{\nHEA", 'adsc'),
                 (b"{", 'edf'),
                 (b"\r{", 'edf'),
                 (b"\n{", 'edf'),
                 (b"ADEPT", 'GE'),
                 (b"OD", 'OXD'),
                 (b"IM", 'HiPiC'),
                 (b'\x2d\x04', 'mar345'),
                 (b'\xd2\x04', 'mar345'),
                 (b'\x04\x2d', 'mar345'),  # some machines may need byteswapping
                 (b'\x04\xd2', 'mar345'),
                 # hint : MASK in 32 bit
                 (b'M\x00\x00\x00A\x00\x00\x00S\x00\x00\x00K\x00\x00\x00', 'fit2dmask'),
                 (b'\x00\x00\x00\x03', 'dm3'),
                 (b"No", "kcd"),
                 (b"<", "xsd"),
                 (b"\n\xb8\x03\x00", 'pixi'),
                 (b"\x89\x48\x44\x46\x0d\x0a\x1a\x0a", "eiger/hdf5"),
                 (b"R-AXIS", 'raxis'),
                 (b"\x93NUMPY", 'numpy'),
                 (b"\\$FFF_START", 'fit2d'),
                ]


def do_magic(byts, filename):
    """ Try to interpret the bytes starting the file as a magic number """
    for magic, format_type in MAGIC_NUMBERS:
        if byts.startswith(magic):
            if "/" in format_type:
                if format_type == "eiger/hdf5":
                    if "::" in filename:
                        return "hdf5"
                    else:
                        return "eiger"
                elif format_type == "marccd/tif":
                    if "mccd" in filename.split("."):
                        return "marccd"
                    else:
                        return "tif"
            return format_type
    raise Exception("Could not interpret magic string")


def openimage(filename, frame=None):
    """ Try to open an image """
    if isinstance(filename, FilenameObject):
        try:
            logger.debug("Attempting to open %s" % (filename.tostring()))
            obj = _openimage(filename.tostring())
            logger.debug("Attempting to read frame %s from %s with reader %s" % (frame, filename.tostring(), obj.classname))
            obj = obj.read(filename.tostring(), frame)
        except Exception as ex:
            # multiframe file
            # logger.debug( "DEBUG: multiframe file, start # %d"%(
            #    filename.num)
            logger.debug("Exception %s, trying name %s" % (ex, filename.stem))
            obj = _openimage(filename.stem)
            logger.debug("Reading frame %s from %s" % (filename.num, filename.stem))
            obj.read(filename.stem, frame=filename.num)
    else:
        logger.debug("Attempting to open %s" % (filename))
        obj = _openimage(filename)
        logger.debug("Attempting to read frame %s from %s with reader %s" % (frame, filename, obj.classname))
        obj = obj.read(obj.filename, frame)
    return obj


def openheader(filename):
    """ return only the header"""
    obj = _openimage(filename)
    obj.readheader(obj.filename)
    return obj


def _openimage(filename):
    """
    determine which format for a filename
    and return appropriate class which can be used for opening the image

    @param filename: can be an url like:

    hdf5:///example.h5?entry/instrument/detector/data/data#slice=[:,:,5]

    """
    try:
        url = urlparse(filename)
    except AttributeError as err:
        # Assume we have as input a BytesIO object
        attrs = dir(filename)
        if "seek" in attrs and "read" in attrs:
            if not isinstance(filename, BytesIO):
                filename.seek(0)
                actual_filename = BytesIO(filename.read())
        else:
            actual_filename = filename
        url = urlparse("")

    else:
        # related to https://github.com/silx-kit/fabio/issues/34
        if (len(url.scheme) == 1 and (sys.platform == "win32")) or url.path.startswith(":"):
            # this is likely a C: from windows  or filename::path
            filename = url.scheme + ":" + url.path
        else:
            filename = url.path
        actual_filename = filename.split("::")[0]

    try:
        imo = FabioImage()
        byts = imo._open(actual_filename).read(18)
        filetype = do_magic(byts, filename)
    except IOError as error:
        logger.error("%s: File probably does not exist", error)
        raise error
    except:
        try:
            file_obj = FilenameObject(filename=filename)
            if file_obj is None:
                raise Exception("Unable to deconstruct filename")
            if (file_obj.format is not None) and\
               len(file_obj.format) != 1 and \
               isinstance(file_obj.format, list):
                # one of OXD/ADSC - should have got in previous
                raise Exception("openimage failed on magic bytes & name guess")
            filetype = file_obj.format

        except Exception as error:
            logger.error(error)
            import traceback
            traceback.print_exc()
            raise Exception("Fabio could not identify " + filename)
    klass_name = "".join(filetype) + 'image'

    try:
        obj = FabioImage.factory(klass_name)
    except RuntimeError as err:
        logger.error("Filetype not known %s %s" % (filename, klass_name))
        raise err

    if url.scheme in ["nxs", "hdf5"] and filetype == "hdf5":
        obj.set_url(url)
    obj.filename = filename
    # skip the read for read header
    return obj





