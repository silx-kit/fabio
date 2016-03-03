# coding: utf-8
#
#    Project: X-ray image reader
#             https://github.com/kif/fabio
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

import sys, logging
logger = logging.getLogger("openimage")
from .fabioutils  import FilenameObject
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

if sys.version_info[0] < 3:
    bytes = str
    from urlparse import urlparse
else:
    from urllib.parse import  urlparse

MAGIC_NUMBERS = [
    # "\42\5a" : 'bzipped'
    # "\1f\8b" : 'gzipped'
    (b"FORMAT :        86" , 'bruker'),
    (b"\x4d\x4d\x00\x2a"   , 'tif') ,
    # The marCCD and Pilatus formats are both standard tif with a header
    # hopefully these byte patterns are unique for the formats
    # If not the image will be read, but the is missing
    (b"\x49\x49\x2a\x00\x08\x00"   , 'marccd') ,
    (b"\x49\x49\x2a\x00\x82\x00"   , 'pilatus') ,
    (b"\x49\x49\x2a\x00"   , 'tif') ,
    # ADSC must come before edf
    (b"{\nHEA"             , 'adsc'),
    (b"{"                  , 'edf'),
    (b"\r{"                , 'edf'),
    (b"\n{"                , 'edf'),
    (b"ADEPT"              , 'GE'),
    (b"OD"                 , 'OXD'),
    (b"IM"                 , 'HiPiC'),
    (b'\x2d\x04'           , 'mar345'),
    (b'\xd2\x04'           , 'mar345'),
    (b'\x04\x2d'           , 'mar345'),  # some machines may need byteswapping
    (b'\x04\xd2'           , 'mar345'),
    # hint : MASK in 32 bit
    (b'M\x00\x00\x00A\x00\x00\x00S\x00\x00\x00K\x00\x00\x00' , 'fit2dmask') ,
    (b'\x00\x00\x00\x03'   , 'dm3'),
    (b"No"                 , "kcd"),
    (b"<"                  , "xsd"),
    (b"\n\xb8\x03\x00"     , 'pixi'),
    (b"\x89\x48\x44\x46"   , 'hdf5'),
    (b"R-AXIS"             , 'raxis'),
    (b"\x93NUMPY"          , 'numpy')
    ]

URL_PREFIX = {"file:":False, "hdf5:":True, "h5:":True, "nxs:": True}

def do_magic(byts):
    """ Try to interpret the bytes starting the file as a magic number """
    for magic, format_type in MAGIC_NUMBERS:
        if byts.find(magic) == 0:
            return format_type
        if 0:  # debugging - bruker needed 18 bytes below
            logger.debug("m: %s f: %s", magic, format_type)
            logger.debug("bytes: %s len(bytes) %s", magic, len(magic))
            logger.debug("found: %s", byts.find(magic))
            for i in range(len(magic)):
                logger.debug("%s %s %s %s ", ord(magic[i]), ord(byts[i]), magic[i], byts[i])
    raise Exception("Could not interpret magic string")


def openimage(filename, frame=None):
    """ Try to open an image """
    if isinstance(filename, FilenameObject):
        try:
            logger.debug("Attempting to open %s" % (filename.tostring()))
            obj = _openimage(filename.tostring())
            logger.debug("Attempting to read frame %s from %s" % (frame,
                filename.tostring()))
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
        logger.debug("Attempting to read frame %s from %s" % (frame, filename))
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
    url = urlparse(filename)

    # related to https://github.com/kif/fabio/issues/34
    if len(url.scheme) == 1 and (sys.platform == "win32"):
        # this is likely a C: from windows
        filename = url.scheme + ":" + url.path
    else:
        filename = url.path

    try:
        imo = FabioImage()
        byts = imo._open(filename).read(18)
        filetype = do_magic(byts)
        if filetype == "marccd" and filename.find("mccd") == -1:
            # Cannot see a way around this. Need to find something
            # to distinguish mccd from regular tif...
            filetype = "tif"
    except IOError as error:
        logger.error("%s: File probably does not exist", error)
        raise error
    except:
        try:
            file_obj = FilenameObject(filename=filename)
            if file_obj == None:
                raise Exception("Unable to deconstruct filename")
            if (file_obj.format is not None) and\
                len(file_obj.format) != 1 and \
                type(file_obj.format) != type(["list"]):
                # one of OXD/ ADSC - should have got in previous
                raise Exception("openimage failed on magic bytes & name guess")
            filetype = file_obj.format
            # UNUSED filenumber = file_obj.num
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





