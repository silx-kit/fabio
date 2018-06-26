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

import os.path
import logging
logger = logging.getLogger(__name__)
from . import fabioutils
from .fabioutils import FilenameObject, six, BytesIO
from .fabioimage import FabioImage

# Make sure to load all formats
from . import fabioformats  # noqa


MAGIC_NUMBERS = [
    # "\42\5a" : 'bzipped'
    # "\1f\8b" : 'gzipped'
    (b"FORMAT :100", 'bruker100'),
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
    # Raw JPEG
    (b"\xFF\xD8\xFF\xDB", "jpeg"),
    # JFIF format
    (b"\xFF\xD8\xFF\xE0", "jpeg"),
    # Exif format
    (b"\xFF\xD8\xFF\xE1", "jpeg"),
    # JPEG 2000 (from RFC 3745)
    (b"\x00\x00\x00\x0C\x6A\x50\x20\x20\x0D\x0A\x87\x0A", "jpeg2k"),
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
    if isinstance(filename, fabioutils.PathTypes):
        if not isinstance(filename, fabioutils.StringTypes):
            filename = str(filename)

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
    if isinstance(filename, fabioutils.PathTypes):
        if not isinstance(filename, fabioutils.StringTypes):
            filename = str(filename)

    obj = _openimage(filename)
    obj.readheader(obj.filename)
    return obj


def _openimage(filename):
    """
    determine which format for a filename
    and return appropriate class which can be used for opening the image

    :param filename: can be an url like:

    hdf5:///example.h5?entry/instrument/detector/data/data#slice=[:,:,5]

    """
    url = None
    if hasattr(filename, "seek") and hasattr(filename, "read"):
        # Looks to be a file containing filenames
        if not isinstance(filename, BytesIO):
            filename.seek(0)
            actual_filename = BytesIO(filename.read())
    else:
        if os.path.exists(filename):
            # Already a valid filename
            actual_filename = filename
        else:
            try:
                url = six.moves.urllib_parse.urlparse(filename)
                actual_filename = url.path.split("::")[0]
            except AttributeError as err:
                actual_filename = filename

    if url is None:
        url = six.moves.urllib_parse.urlparse("")

    try:
        imo = FabioImage()
        with imo._open(actual_filename) as f:
            magic_bytes = f.read(18)
    except IOError as error:
        logger.debug("%s: File probably does not exist", error)
        raise error
    else:
        imo = None

    filetype = None
    try:
        filetype = do_magic(magic_bytes, filename)
    except Exception:
        logger.debug("Backtrace", exc_info=True)
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
            logger.debug("Backtrace", exc_info=True)
            raise IOError("Fabio could not identify " + filename)

    if filetype is None:
        raise IOError("Fabio could not identify " + filename)

    klass_name = "".join(filetype) + 'image'

    try:
        obj = FabioImage.factory(klass_name)
    except (RuntimeError, Exception):
        logger.debug("Backtrace", exc_info=True)
        raise IOError("Filename %s can't be read as format %s" % (filename, klass_name))

    if url.scheme in ["nxs", "hdf5"] and filetype == "hdf5":
        obj.set_url(url)
    obj.filename = filename
    # skip the read for read header
    return obj
