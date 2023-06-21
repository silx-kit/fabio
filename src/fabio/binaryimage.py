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

"""
Authors: Gael Goret, Jerome Kieffer, ESRF, France

Emails: gael.goret@esrf.fr, jerome.kieffer@esrf.fr
        Brian Richard Pauw <brian@stack.nl>

Binary files images are simple none-compressed 2D images only defined by their :
data-type, dimensions, byte order and offset

This simple library has been made for manipulating exotic/unknown files format.
"""

__authors__ = ["Gaël Goret", "Jérôme Kieffer", "Brian Pauw"]
__contact__ = "gael.goret@esrf.fr"
__license__ = "MIT"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__version__ = "17/10/2012"

import io
from .fabioimage import FabioImage
import numpy
import logging
logger = logging.getLogger(__name__)


class BinaryImage(FabioImage):
    """
    This simple library has been made for manipulating exotic/unknown files format.

    Binary files images are simple none-compressed 2D images only defined by their:
        data-type, dimensions, byte order and offset

    if offset is set to a negative value, the image is read using the last data but n
    data in the file, skipping any header.
    """

    DESCRIPTION = "Binary format (none-compressed 2D images)"

    DEFAULT_EXTENSIONS = ["bin"]

    def __init__(self, *args, **kwargs):
        FabioImage.__init__(self, *args, **kwargs)

    @staticmethod
    def swap_needed(endian):
        """
        Decide if we need to byteswap
        """
        if (endian == '<' and numpy.little_endian) or (endian == '>' and not numpy.little_endian):
            return False
        if (endian == '>' and numpy.little_endian) or (endian == '<' and not numpy.little_endian):
            return True

    def read(self, fname, dim1, dim2, offset=0, bytecode="int32", endian="<"):
        """
        Read a binary image

        :param str fname: file name
        :param int dim1: image dimensions (Fast index)
        :param int dim2: image dimensions (Slow index)
        :param int offset: starting position of the data-block. If negative, starts at the end.
        :param bytecode: can be "int8","int16","int32","int64","uint8","uint16","uint32","uint64","float32","float64",...
        :param endian:  among short or long endian ("<" or ">")

        """
        self.filename = fname
        self._shape = dim2, dim1
        self._bytecode = bytecode
        with open(self.filename, "rb") as f: 
            dims = [dim2, dim1]
            bpp = numpy.dtype(bytecode).itemsize
            size = dims[0] * dims[1] * bpp
    
            if offset >= 0:
                f.seek(offset)
            else:
                try:
                    f.seek(-size + offset + 1, 2)  # seek from EOF backwards
                except IOError:
                    logger.warning('expected datablock too large, please check bytecode settings: {}'.format(bytecode))
                except Exception:
                    logger.debug("Backtrace", exc_info=True)
                    logger.error('Uncommon error encountered when reading file')
            rawData = f.read(size)
        data = numpy.frombuffer(rawData, bytecode).copy().reshape(tuple(dims))
        if self.swap_needed(endian):
            data.byteswap(True)
        self.data = data
        self._shape = None
        return self

    def estimate_offset_value(self, fname, dim1, dim2, bytecode="int32"):
        "Estimates the size of a file"
        with open(fname, "rb") as f:
            bpp = len(numpy.array(0, bytecode).tobytes())
            size = dim1 * dim2 * bpp
            totsize = len(f.read())
        logger.info('total size (bytes): %s', totsize)
        logger.info('expected data size given parameters (bytes): %s', size)
        logger.info('estimation of the offset value (bytes): %s', totsize - size)

    def write(self, fname):
        with self._open(fname, mode="wb") as outfile:
            if isinstance(outfile, io.BufferedWriter):
                self.data.tofile(outfile)
            else:
                outfile.write(self.data.tobytes())


binaryimage = BinaryImage
