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

"""FabIO reader for Fit2D binary images

TODO: handle big-endian files
"""

__authors__ = ["Jérôme Kieffer"]
__contact__ = "jerome.kiefer@esrf.fr"
__license__ = "MIT"
__copyright__ = "2016-2016 European Synchrotron Radiation Facility"
__date__ = "09/02/2023"

import logging
logger = logging.getLogger(__name__)
import numpy
from .fabioimage import FabioImage, OrderedDict


def hex_to(stg, type_="int"):
    """convert a 8-byte-long string (bytes) into an int or a float

    :param stg: bytes string
    :param str type_: "int" or "float"
    """
    value = int(stg, 16)
    if type_ == "float":
        value = numpy.array([int("38d1b717", 16)], "int32").view("float32")[0]
    return value


class Fit2dImage(FabioImage):
    """
    FabIO image class for Images for XXX detector
    """

    DESCRIPTION = "Fit2d file format"

    DEFAULT_EXTENSIONS = ["f2d"]

    BUFFER_SIZE = 512  # size of the buffer
    PIXELS_PER_CHUNK = 128
    ENC = "ascii"

    def __init__(self, *arg, **kwargs):
        """
        Generic constructor
        """
        FabioImage.__init__(self, *arg, **kwargs)
        self.num_block = None

    def _readheader(self, infile):
        """
        Read and decode the header of an image:

        :param infile: Opened python file (can be stringIO or bipped file)
        """
        # list of header key to keep the order (when writing)
        header = OrderedDict()
        self.header = self.check_header()

        while True:
            line = infile.read(self.BUFFER_SIZE)
            if len(line) < self.BUFFER_SIZE:
                break
            if line[0:1] != b"\\":
                for block_read in range(2, 16):
                    line = infile.read(self.BUFFER_SIZE)
                    if line[0:1] == b"\\":
                        self.BUFFER_SIZE *= block_read
                        logger.warning("Increase block size to %s ", self.BUFFER_SIZE)
                        infile.seek(0)
                        break
                else:
                    err = "issue while reading header, expected '\', got %s" % line[0]
                    logger.error(err)
                    raise RuntimeError(err)
            key, line = line.split(b":", 1)
            num_block = hex_to(line[:8])
            metadatatype = line[8:9].decode(self.ENC)
            key = key[1:].decode(self.ENC)
            if metadatatype == "s":
                len_value = hex_to(line[9:17])
                header[key] = line[17:17 + len_value].decode(self.ENC)
            elif metadatatype == "r":
                header[key] = hex_to(line[9:17], "float")
            elif metadatatype == "i":
                header[key] = hex_to(line[9:17])
            elif metadatatype == "a" and num_block != 0:  # "a"
                self.num_block = num_block
                array_type = line[9:10].decode(self.ENC)
                dim1 = hex_to(line[26:34])
                dim2 = hex_to(line[34:42])
                if array_type == "i":
                    bytecode = "int32"
                    bpp = 4
                elif array_type == "r":
                    bytecode = "float32"
                    bpp = 4
                elif array_type == "l":
                    bytecode = "int8"
                    bpp = 1
                    raw = infile.read(self.num_block * self.BUFFER_SIZE)
                    # Fit2d stores 31 pixels per int32
                    i32 = numpy.frombuffer(raw, numpy.int32).copy()
                    if numpy.little_endian:
                        # lets's work in big-endian for the moment
                        i32.byteswap(True)
                    r32 = numpy.unpackbits(i32.view("uint8")).reshape((-1, 32))
                    # Remove the sign bit which is the first in big-endian
                    # all pixels are in reverse order in the group of 31
                    r31 = r32[:, -1:0:-1]
                    mask = r31.ravel()[:dim1 * dim2].reshape((dim2, dim1))
                    header[key] = mask
                    continue
                else:
                    err = "unsupported data type: %s" % array_type
                    logger.error(err)
                    raise RuntimeError(err)
                raw = infile.read(self.num_block * self.BUFFER_SIZE)
                decoded = numpy.frombuffer(raw, bytecode).copy().reshape((-1, self.BUFFER_SIZE // bpp))
                # There is a bug in this format: throw away 3/4 of the read data:
                decoded = decoded[:, :self.PIXELS_PER_CHUNK].ravel()
                header[key] = decoded[:dim1 * dim2].reshape(dim2, dim1)
        self.header = header

    def read(self, fname, frame=None):
        """try to read image

        :param fname: name of the file
        """

        self.resetvals()
        with self._open(fname) as infile:
            self._readheader(infile)
        self.data = self.header.pop("data_array")
        return self


# this is for compatibility with old code:
fit2dimage = Fit2dImage
