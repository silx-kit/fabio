# -*- coding: utf-8 -*-
#cython: embedsignature=True, language_level=3
## This is for optimisation
#cython: boundscheck=False, wraparound=False, cdivision=True, initializedcheck=False,
## This is for developping:
##cython: profile=True, warn.undeclared=True, warn.unused=True, warn.unused_result=False, warn.unused_arg=True
#
#    Project: Fable Input/Output
#             https://github.com/silx-kit/fabio
#
#    Copyright (C) 2020-2020 European Synchrotron Radiation Facility, Grenoble, France
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

"""Compression and decompression extension for Esperanto format
"""
__author__ = "Jérôme Kieffer"
__date__ = "10/11/2020"
__contact__ = "Jerome.kieffer@esrf.fr"
__license__ = "MIT"

from io import BytesIO
from struct import pack
import numpy

from libc.stdint cimport int32_t, int64_t, uint64_t 
ctypedef fused any_int:
    int32_t
    int64_t

cpdef int32_t fieldsize(any_int nbvalue):
    "Direct translation of Fortran"
    cdef int getfieldsize
    if(nbvalue < -63):
        getfieldsize = 8
    elif(nbvalue < -31):
        getfieldsize = 7
    elif(nbvalue < -15):
        getfieldsize = 6
    elif(nbvalue < -7):
        getfieldsize = 5
    elif(nbvalue < -3):
        getfieldsize = 4
    elif(nbvalue < -1):
        getfieldsize = 3
    elif(nbvalue < 0):
        getfieldsize = 2
    elif(nbvalue < 2):
        getfieldsize = 1
    elif(nbvalue < 3):
        getfieldsize = 2
    elif(nbvalue < 5):
        getfieldsize = 3
    elif(nbvalue < 9):
        getfieldsize = 4
    elif(nbvalue < 17):
        getfieldsize = 5
    elif(nbvalue < 33):
        getfieldsize = 6
    elif(nbvalue < 65):
        getfieldsize = 7
    else:
        getfieldsize = 8
    return getfieldsize


cpdef int32_t get_fieldsize(any_int[::1] array):
    """determine the fieldsize to store the given values
    
    :param array numpy.array
    :returns int
    """
    cdef:
        any_int maxi, mini, value
        int32_t size, idx, 
    maxi = mini = 0
    size = array.shape[0]
    for idx in range(size):
        value = array[idx]
        maxi = max(maxi, value)
        mini = min(mini, value)
    
    return max(fieldsize(maxi), fieldsize(mini))


cpdef write_escaped(int32_t value, buffer):
    """write an value to the buffer and escape when overflowing one byte
    :param value: int
    :param buffer: io.BytesIO
    """
    if -127 <= value < 127:
        buffer.write(pack("B", value + 127))
    elif -32767 < value < 32767:
        buffer.write(b'\xfe' + pack("<h", value))
    else:
        buffer.write(b'\xff' + pack("<i", value))


cpdef bytes compress_field(int32_t[::1] ifield, int32_t fieldsize, overflow_table):
    """compress a field with given size
    :param ifield: numpy.ndarray
    :param fieldsize: int
    :param overflow_table: io.BytesIO
    :returns: bytes
    """
    cdef:
        uint64_t compressed_field, i, val, conv_
    if fieldsize == 8:
        # we have to deal offsets but not bitshifts
        tmp = bytearray(8)
        for i in range(8):
            elem = ifield[i]
            if -127 <= elem < 127:
                tmp[i] = elem + 127
            elif -32767 <= elem < 32767:
                tmp[i] = 254
                overflow_table.write(pack("<h", elem))
            else:
                tmp[i] = 255
                overflow_table.write(pack("<i", elem))
        return bytes(tmp)
    elif fieldsize > 0:
        # we have to deal with bit-shifts but not offsets
        conv_ = (1<<(fieldsize - 1)) - 1 
        compressed_field = 0
        for i in range(8):
            val = ifield[i] + conv_
            compressed_field |= val << (i * fieldsize)
        try:
            res = pack("<Q", compressed_field)
        except:
            print("Exception in struct.pack: %s %s %s %s", fieldsize, type(fieldsize), ifield, compressed_field)
            raise
        return res[:fieldsize]
    else:
        raise AssertionError("fieldsize is between 0 and 8")


def compress_row(int32_t[::1] data, buffer):
    """compress a single row
    :arg data numpy.array
    :arg buffer io.BytesIO
    """
    cdef:
        int32_t size, first_pixel, n_fields, n_restpx, len_a, len_b, cur, prev, i
        int32_t[::1] fielda, fieldb, pixel_diff
    
    size = data.shape[0]
    first_pixel = data[0]
    #data[1:] - data[:size-1]
    pixel_diff = numpy.empty(size-1, dtype=numpy.int32)
    
    prev = first_pixel
    for i in range(1, size):
        cur = data[i]
        pixel_diff[i-1] = cur - prev
        prev = cur

    write_escaped(first_pixel, buffer)

    n_fields = (size-1) // 16
    n_restpx = (size-1) % 16

    for i in range(n_fields):
        fielda = pixel_diff[:8]
        fieldb = pixel_diff[8:16]

        len_a = get_fieldsize(fielda)
        len_b = get_fieldsize(fieldb)
        len_byte = (len_b << 4) | len_a
        buffer.write(pack("B", len_byte))

        of_buff = BytesIO()
        compressed_fielda = compress_field(fielda, len_a, of_buff)
        compressed_fieldb = compress_field(fieldb, len_b, of_buff)

        buffer.write(compressed_fielda + compressed_fieldb + of_buff.getvalue())

        pixel_diff = pixel_diff[16:]

    for i in range(n_restpx):
        write_escaped(pixel_diff[i], buffer)
        