#!/usr/bin/env python
# coding: utf-8

"""
Author: Andy Hammersley, ESRF
Translation into python/fabio: Jon Wright, ESRF.
Writer: Jérôme Kieffer
"""
# Get ready for python3:
from __future__ import with_statement, print_function

__authors__ = ["Jon Wright", "Jérôme Kieffer"]
__contact__ = "Jerome.Kieffer@esrf.fr"
__license__ = "GPLv3+"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__version__ = "06/01/2015"

import numpy
import sys
import struct
from .fabioimage import fabioimage
if sys.version < '3':
    bytes = str


class fit2dmaskimage(fabioimage):
    """ Read and try to write Andy Hammersley's mask format """


    def _readheader(self, infile):
        """
        Read in a header from an already open file
        """
        # 1024 bytes gives 256x32 bit integers
        header = infile.read(1024)
        for i, j in [ (b"M", 0),
                      (b"A", 4),
                      (b"S", 8),
                      (b"K", 12)  ]:
            if header[j] != i[0]:
                raise Exception("Not a fit2d mask file")
        fit2dhdr = numpy.fromstring(header, numpy.int32)
        self.dim1 = fit2dhdr[4]  # 1 less than Andy's fortran
        self.dim2 = fit2dhdr[5]


    def read(self, fname, frame=None):
        """
        Read in header into self.header and
            the data   into self.data
        """
        fin = self._open(fname)
        self._readheader(fin)
        # Compute image size
        self.bytecode = numpy.uint8
        self.bpp = len(numpy.array(0, self.bytecode).tostring())

        # integer division
        num_ints = (self.dim1 + 31) // 32
        total = self.dim2 * num_ints * 4
        data = fin.read(total)
        assert len(data) == total
        fin.close()

        # Now to unpack it
        data = numpy.fromstring(data, numpy.uint8)
        data = numpy.reshape(data, (self.dim2, num_ints * 4))

        result = numpy.zeros((self.dim2, num_ints * 4 * 8), numpy.uint8)

        # Unpack using bitwise comparisons to 2**n
        bits = numpy.ones((1), numpy.uint8)
        for i in range(8):
            temp = numpy.bitwise_and(bits, data)
            result[:, i::8] = temp.astype(numpy.uint8)
            bits = bits * 2
        # Extra rows needed for packing odd dimensions
        spares = num_ints * 4 * 8 - self.dim1
        if spares == 0:
            self.data = numpy.where(result == 0, 0, 1)
        else:
            self.data = numpy.where(result[:, :-spares] == 0, 0, 1)
        # Transpose appears to be needed to match edf reader (scary??)
#        self.data = numpy.transpose(self.data)
        self.data = numpy.reshape(self.data.astype(numpy.uint16),
                                    (self.dim2, self.dim1))
        self.pilimage = None
        return self



    def write(self, fname):
        """
        Try to write a file
        """
        header = bytearray(b"\x00"*1024)
        header[0] = 77  # M
        header[4] = 65  # A
        header[8] = 83  # S
        header[12] = 75  # K
        header[24] = 1  # 1
        str1 = struct.pack("I", self.dim1)
        str2 = struct.pack("I", self.dim2)
        if not numpy.little_endian:
            str1 = str1[-1::-1]
            str2 = str2[-1::-1]
        header[16:20] = str1
        header[20:24] = str2
        compact_array = numpy.zeros((self.dim2, ((self.dim1 + 31) // 32) * 4), dtype=numpy.uint8)
        large_array = numpy.zeros((self.dim2, ((self.dim1 + 31) // 32) * 32), dtype=numpy.uint8)
        large_array[:self.dim2, :self.dim1] = (self.data != 0)
        for i in range(8):
            order = (1 << i)
            compact_array += large_array[:, i::8] * order
        with self._open(fname, mode="wb") as outfile:
            outfile.write(bytes(header))
            outfile.write(compact_array.tostring())

    @staticmethod
    def checkData(data=None):
        if data is None:
            return None
        else:
            return data.astype(int)
