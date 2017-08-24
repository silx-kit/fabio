# coding: utf-8
#
#    Project: FabIO X-ray image reader
#
#    Copyright (C) 2010-2016 European Synchrotron Radiation Facility
#                       Grenoble, France
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
# THE SOFTWARE.
#

"""
FabIO class for dealing with TIFF images.
In facts wraps TiffIO from V. Armando Solé (available in PyMca) or falls back to PIL

Authors:
........
* Henning O. Sorensen & Erik Knudsen:
  Center for Fundamental Research: Metal Structures in Four Dimensions;
  Risoe National Laboratory;
  Frederiksborgvej 399;
  DK-4000 Roskilde;
  email:erik.knudsen@risoe.dk
* Jérôme Kieffer:
  European Synchrotron Radiation Facility;
  Grenoble (France)

License: MIT
"""
# Get ready for python3:
from __future__ import with_statement, print_function, division

__authors__ = ["Jérôme Kieffer", "Henning O. Sorensen", "Erik Knudsen"]
__date__ = "11/08/2017"
__license__ = "MIT"
__copyright__ = "ESRF, Grenoble & Risoe National Laboratory"
__status__ = "stable"

import time
import logging
import struct
logger = logging.getLogger(__name__)

try:
    from PIL import Image
except ImportError:
    Image = None
import numpy
from .utils import pilutils
from .fabioimage import FabioImage
from .TiffIO import TiffIO

LITTLE_ENDIAN = 1234
BIG_ENDIAN = 3412

TYPES = {
    0: 'invalid',
    1: 'byte',
    2: 'ascii',
    3: 'short',
    4: 'long',
    5: 'rational',
    6: 'sbyte',
    7: 'undefined',
    8: 'sshort',
    9: 'slong',
    10: 'srational',
    11: 'float',
    12: 'double'
}

TYPESIZES = {
    0: 0,
    1: 1,
    2: 1,
    3: 2,
    4: 4,
    5: 8,
    6: 1,
    7: 1,
    8: 2,
    9: 4,
    10: 8,
    11: 4,
    12: 8
}

baseline_tiff_tags = {
    256: 'ImageWidth',
    257: 'ImageLength',
    306: 'DateTime',
    315: 'Artist',
    258: 'BitsPerSample',
    265: 'CellLength',
    264: 'CellWidth',
    259: 'Compression',

    262: 'PhotometricInterpretation',
    296: 'ResolutionUnit',
    282: 'XResolution',
    283: 'YResolution',

    278: 'RowsPerStrip',
    273: 'StripOffset',
    279: 'StripByteCounts',

    270: 'ImageDescription',
    271: 'Make',
    272: 'Model',
    320: 'ColorMap',
    305: 'Software',
    339: 'SampleFormat',
    33432: 'Copyright'
}


class TifImage(FabioImage):
    """
    Images in TIF format
    Wraps TiffIO
    """
    DESCRIPTION = "Tagged image file format"

    DEFAULT_EXTENTIONS = ["tif", "tiff"]

    _need_a_seek_to_read = True

    def __init__(self, *args, **kwds):
        """ Tifimage constructor adds an nbits member attribute """
        self.nbits = None
        FabioImage.__init__(self, *args, **kwds)
        self.lib = None

    def _readheader(self, infile):
        """
        Try to read Tiff images header...
        """
        # try:
        #     self.header = { "filename" : infile.name }
        # except AttributeError:
        #     self.header = {}
        # t = Tiff_header(infile.read())
        # self.header = t.header
        # try:
        #     self.dim1 = int(self.header['ImageWidth'])
        #     self.dim2 = int(self.header['ImageLength'])
        # except (KeyError):
        #     logger.warning("image dimensions could not be determined from header tags, trying to go on anyway")
        # read the first 32 bytes to determine size
        header = numpy.fromstring(infile.read(64), numpy.uint16)
        self.dim1 = int(header[9])
        self.dim2 = int(header[15])
        # nbits is not a FabioImage attribute...
        self.nbits = int(header[21])  # number of bits

    def read(self, fname, frame=None):
        """
        Wrapper for TiffIO.
        """
        infile = self._open(fname, "rb")
        self._readheader(infile)
        infile.seek(0)
        self.lib = None
        try:
            tiffIO = TiffIO(infile)
            if tiffIO.getNumberOfImages() > 0:
                # No support for now of multi-frame tiff images
                self.data = tiffIO.getImage(0)
                self.header = tiffIO.getInfo(0)
        except Exception as error:
            logger.warning("Unable to read %s with TiffIO due to %s, trying PIL" % (fname, error))
        else:
            if self.data.ndim == 2:
                self.dim2, self.dim1 = self.data.shape
            elif self.data.ndim == 3:
                self.dim2, self.dim1, _ = self.data.shape
                logger.warning("Third dimension is the color")
            else:
                logger.warning("dataset has %s dimensions (%s), check for errors !!!!", self.data.ndim, self.data.shape)
            self.lib = "TiffIO"

        if (self.lib is None):
            if Image:
                try:
                    infile.seek(0)
                    self.pilimage = Image.open(infile)
                except Exception:
                    logger.error("Error in opening %s  with PIL" % fname)
                    self.lib = None
                    infile.seek(0)
                else:
                    self.lib = "PIL"
                    self.data = pilutils.get_numpy_array(self.pilimage)
            else:
                logger.error("Error in opening %s: no tiff reader managed to read the file.", fname)
                self.lib = None
                infile.seek(0)

        self.resetvals()
        return self

    def write(self, fname):
        """
        Overrides the FabioImage.write method and provides a simple TIFF image writer.

        :param str fname: name of the file to save the image to
        """
        with TiffIO(fname, mode="w") as tIO:
            tIO.writeImage(self.data, info=self.header, software="fabio.tifimage", date=time.ctime())


# define a couple of helper classes here:
class Tiff_header(object):
    def __init__(self, string):
        if string[:4] == "II\x2a\x00":
            self.byteorder = LITTLE_ENDIAN
        elif string[:4] == 'MM\x00\x2a':
            self.byteorder = BIG_ENDIAN
        else:
            logger.warning("Warning: This does not appear to be a tiff file")
        # the next two bytes contains the offset of the oth IFD
        offset_first_ifd = struct.unpack_from("h", string[4:])[0]
        self.ifd = [Image_File_Directory()]
        offset_next = self.ifd[0].unpack(string, offset_first_ifd)
        while (offset_next != 0):
            self.ifd.append(Image_File_Directory())
            offset_next = self.ifd[-1].unpack(string, offset_next)

        self.header = {}
        # read the values of the header items into a dictionary
        for entry in self.ifd[0].entries:
            if entry.tag in baseline_tiff_tags.keys():
                self.header[baseline_tiff_tags[entry.tag]] = entry.val
            else:
                self.header[entry.tag] = entry.val


class Image_File_Directory(object):
    def __init__(self, instring=None, offset=-1):
        self.entries = []
        self.offset = offset
        self.count = None

    def unpack(self, instring, offset=-1):
        if (offset == -1):
            offset = self.offset

        strInput = instring[offset:]
        self.count = struct.unpack_from("H", strInput[:2])[0]
        # 0th IFD contains count-1 entries (count includes the adress of the next IFD)
        for i in range(self.count - 1):
            e = Image_File_Directory_entry().unpack(strInput[2 + 12 * (i + 1):])
            if (e is not None):
                self.entries.append(e)
            # extract data associated with tags
            for e in self.entries:
                if (e.val is None):
                    e.extract_data(instring)
        # do we have some more ifds in this file
        offset_next = struct.unpack_from("L", instring[offset + 2 + self.count * 12:])[0]
        return offset_next


class Image_File_Directory_entry(object):
    def __init__(self, tag=0, tag_type=0, count=0, offset=0):
        self.tag = tag
        self.tag_type = tag_type
        self.count = count
        self.val_offset = offset
        self.val = None

    def unpack(self, strInput):
        idfentry = strInput[:12]
################################################################################
# #        TOFIX: How is it possible that HHL (2+2+4 bytes has a size of )
################################################################################
        (tag, tag_type, count) = struct.unpack_from("HHL", idfentry)
        self.tag = tag
        self.count = count
        self.tag_type = tag_type
        self.val = None
        if (count <= 0):
            logger.warning("Tag # %s has an invalid count: %s. Tag is ignored" % (tag, count))
            return
        if(count * TYPESIZES[tag_type] <= 4):
            self.val_offset = 8
            self.extract_data(idfentry)
            self.val_offset = None
        else:
            self.val_offset = struct.unpack_from("L", idfentry[8:])[0]
        return self

    def extract_data(self, full_string):
        tag_type = self.tag_type
        if (TYPES[tag_type] == 'byte'):
            self.val = struct.unpack_from("B", full_string[self.val_offset:])[0]
        elif (TYPES[tag_type] == 'short'):
            self.val = struct.unpack_from("H", full_string[self.val_offset:])[0]
        elif (TYPES[tag_type] == 'long'):
            self.val = struct.unpack_from("L", full_string[self.val_offset:])[0]
        elif (TYPES[tag_type] == 'sbyte'):
            self.val = struct.unpack_from("b", full_string[self.val_offset:])[0]
        elif (TYPES[tag_type] == 'sshort'):
            self.val = struct.unpack_from("h", full_string[self.val_offset:])[0]
        elif (TYPES[tag_type] == 'slong'):
            self.val = struct.unpack_from("l", full_string[self.val_offset:])[0]
        elif (TYPES[tag_type] == 'ascii'):
            self.val = full_string[self.val_offset:self.val_offset + max(self.count, 4)]
        elif (TYPES[tag_type] == 'rational'):
            if self.val_offset is not None:
                (num, den) = struct.unpack_from("LL", full_string[self.val_offset:])
                self.val = float(num) / den
        elif (TYPES[tag_type] == 'srational'):
            if self.val_offset is not None:
                (num, den) = struct.unpack_from("ll", full_string[self.val_offset:])
                self.val = float(num) / den,
        elif (TYPES[tag_type] == 'float'):
            self.val = struct.unpack_from("f", full_string[self.val_offset:])[0]
        elif (TYPES[tag_type] == 'double'):
            if self.val_offset is not None:
                self.val = struct.unpack_from("d", full_string[self.val_offset:])[0]
        else:
            logger.warning("unrecognized type of strInputentry self: %s tag: %s type: %s TYPE: %s" % (self, baseline_tiff_tags[self.tag], self.tag_type, TYPES[tag_type]))


tifimage = TifImage
