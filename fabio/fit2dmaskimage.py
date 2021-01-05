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
# THE SOFTWARE.
#

"""
Author: Andy Hammersley, ESRF
Translation into python/fabio: Jon Wright, ESRF.
Writer: Jérôme Kieffer
"""

__authors__ = ["Jon Wright", "Jérôme Kieffer"]
__contact__ = "Jerome.Kieffer@esrf.fr"
__license__ = "MIT"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__version__ = "06/01/2015"

import io
import numpy
import struct

from .fabioimage import FabioImage


class Fit2dMaskImage(FabioImage):
    """ Read and try to write Andy Hammersley's mask format """

    DESCRIPTION = "Fit2d mask file format"

    DEFAULT_EXTENSIONS = ["msk"]

    def _readheader(self, infile):
        """
        Read in a header from an already open file
        """
        # 1024 bytes gives 256x32 bit integers
        header = infile.read(1024)
        for i, j in [(b"M", 0),
                     (b"A", 4),
                     (b"S", 8),
                     (b"K", 12)]:
            if header[j] != i[0]:
                raise Exception("Not a fit2d mask file")
        fit2dhdr = numpy.frombuffer(header, numpy.int32)
        # Enforce little endian
        if not numpy.little_endian:
            fit2dhdr.byteswap(True)
        dim1 = fit2dhdr[4]  # 1 less than Andy's fortran
        dim2 = fit2dhdr[5]
        self._shape = dim2, dim1

    def read(self, fname, frame=None):
        """
        Read in header into self.header and
            the data   into self.data
        """
        fin = self._open(fname)
        self._readheader(fin)
        # Compute image size
        self._dtype = numpy.dtype(numpy.uint8)

        # integer division
        dim2, dim1 = self._shape
        num_ints = (dim1 + 31) // 32
        total = dim2 * num_ints * 4
        data = fin.read(total)
        assert len(data) == total
        fin.close()

        # Now to unpack it
        data = numpy.frombuffer(data, numpy.uint8)
        if not numpy.little_endian:
            data.byteswap(True)

        data = numpy.reshape(data, (dim2, num_ints * 4))

        result = numpy.zeros((dim2, num_ints * 4 * 8), numpy.uint8)

        # Unpack using bitwise comparisons to 2**n
        bits = numpy.ones((1), numpy.uint8)
        for i in range(8):
            temp = numpy.bitwise_and(bits, data)
            result[:, i::8] = temp.astype(numpy.uint8)
            bits = bits * 2
        # Extra rows needed for packing odd dimensions
        spares = num_ints * 4 * 8 - dim1
        if spares == 0:
            data = numpy.where(result == 0, 0, 1)
        else:
            data = numpy.where(result[:,:-spares] == 0, 0, 1)
        # Transpose appears to be needed to match edf reader (scary??)
        # self.data = numpy.transpose(self.data)
        self.data = numpy.ascontiguousarray(data, dtype=numpy.uint8)
        self.data.shape = self._shape
        self._shape = None
        return self

    def write(self, fname):
        """
        Try to write a file
        """
        dim2, dim1 = self.shape
        header = bytearray(b"\x00" * 1024)
        header[0] = 77  # M
        header[4] = 65  # A
        header[8] = 83  # S
        header[12] = 75  # K
        header[24] = 1  # 1
        header[16:20] = struct.pack("<I", dim1)
        header[20:24] = struct.pack("<I", dim2)
        compact_array = numpy.zeros((dim2, ((dim1 + 31) // 32) * 4), dtype=numpy.uint8)
        large_array = numpy.zeros((dim2, ((dim1 + 31) // 32) * 32), dtype=numpy.uint8)
        large_array[:dim2,:dim1] = (self.data != 0)
        for i in range(8):
            order = (1 << i)
            compact_array += large_array[:, i::8] * order
        with self._open(fname, mode="wb") as outfile:
            outfile.write(bytes(header))
            if isinstance(outfile, io.BufferedWriter):
                compact_array.tofile(outfile)
            else:
                outfile.write(compact_array.tobytes())

    @staticmethod
    def check_data(data=None):
        if data is None:
            return None
        else:
            return (data != 0).astype(numpy.uint8)


fit2dmaskimage = Fit2dMaskImage
