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
__date__ = "13/11/2020"
__contact__ = "Jerome.kieffer@esrf.fr"
__license__ = "MIT"

from io import BytesIO
from struct import pack
import numpy
from libc.stdint cimport int32_t, int64_t, uint64_t, uint32_t, uint8_t, uint16_t, int16_t
ctypedef fused any_int:
    int32_t
    int64_t

cpdef int32_t fieldsize(any_int nbvalue):
    "Direct translation of Fortran"
    return _fieldsize(nbvalue)

cdef uint8_t _fieldsize(any_int nbvalue) nogil:
    "Direct translation of Fortran"
    cdef uint8_t getfieldsize
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

cdef uint8_t _get_fieldsize(int32_t[::1] array) nogil:
    """determine the fieldsize to store the given values
    
    :param array numpy.array
    :returns int
    """
    cdef:
        int32_t maxi, mini, value
        int32_t size, idx, 
    maxi = mini = 0
    size = array.shape[0]
    for idx in range(size):
        value = array[idx]
        maxi = max(maxi, value)
        mini = min(mini, value)
    
    return max(_fieldsize(maxi), _fieldsize(mini))


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

cdef uint16_t _write_escaped(int32_t value, uint8_t[::1] buffer, uint16_t position) nogil:
    """write an value to the buffer at the given position and escape when overflowing one byte
    :param value: int
    :param buffer: compressed line
    :param position: where to start writing in the buffer
    :return: now position in the vector 
    """
    cdef:
        int16_t value_16
        int32_t value_32
        int64_t one=1
        
    if -127 <= value < 127:
        buffer[position] = <uint8_t> (value + 127)
        return position+1
    elif -32767 < value < 32767:
        buffer[position] = 254
        value_16 = value 
        buffer[position+1] = <uint8_t>(value_16 & ((one<<8)-1))
        buffer[position+2] = <uint8_t>((value_16 & ((one<<16)-1))>>8)
        return position+3 
    else:
        buffer[position] = 255
        buffer[position+1] = <uint8_t>((value & ((one<<8)-1)))
        buffer[position+2] = <uint8_t>((value & ((one<<16)-1))>>8) 
        buffer[position+3] = <uint8_t>((value & ((one<<24)-1))>>16)
        buffer[position+4] = <uint8_t>((value & ((one<<32)-1))>>24)
        return position+5 


cpdef bytes compress_field(int32_t[::1] ifield, int32_t fieldsize, overflow_table):
    """compress a field with given size
    :param ifield: numpy.ndarray
    :param fieldsize: int
    :param overflow_table: io.BytesIO
    :returns: bytes
    """
    cdef:
        uint64_t compressed_field, i, val, conv_
        int32_t elem

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
    
cdef uint16_t _compress_field(int32_t[::1] ifield, int32_t fieldsize, uint8_t[::1] buffer, uint16_t position, uint16_t overflow_position) nogil:
    """compress a field with given size
    :param ifield: numpy.ndarray with 8 data to be compressed
    :param fieldsize: int size of the field, number of bits per item
    :param buffer: the output buffer with compressed data
    :param position: Where to write the bitfield in the buffer
    :param overflow_position: Where to write the overflow table in the buffer
    :returns: position of th endd of the overflow values 
    """
    cdef:
        uint64_t compressed_field, i, val, conv_, one
        int32_t value
        int16_t value_16
    if fieldsize == 8:
        # we have to deal offsets but not bitshifts
        one = 1
        for i in range(8):
            value = ifield[i]
            if -127 <= value < 127:
                buffer[position+i] = value + 127
            elif -32767 <= value < 32767:
                buffer[position+i] = 254
                value_16 = value
                buffer[overflow_position] = <uint8_t>(value_16 & ((one<<8)-1))
                buffer[overflow_position+1] = <uint8_t>((value_16 & ((one<<16)-1))>>8)
                overflow_position += 2
            else:
                buffer[position+i] =  255
                buffer[overflow_position] = <uint8_t>((value & ((one<<8)-1)))
                buffer[overflow_position+1] = <uint8_t>((value & ((one<<16)-1))>>8) 
                buffer[overflow_position+2] = <uint8_t>((value & ((one<<24)-1))>>16)
                buffer[overflow_position+3] = <uint8_t>((value & ((one<<32)-1))>>24)
                overflow_position += 4
        return overflow_position
    elif fieldsize > 0:
        # we have to deal with bit-shifts but not offsets
        conv_ = (1<<(fieldsize - 1)) - 1 
        compressed_field = 0
        for i in range(8):
            val = ifield[i] + conv_
            compressed_field |= val << (i * fieldsize)
        for i in range(<uint64_t>fieldsize):
            buffer[position+i] =  <uint8_t>((compressed_field>>(i*8)) & 255)
        return overflow_position
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
        
cdef uint16_t _compress_row(int32_t [::1] data, uint8_t[::1] buffer, int32_t[::1] pixel_diff) nogil:
    """compress a single row
    :param data: numpy.array one line of the input frame
    :param buffer: buffer where to store compressed data
    :return: size of the compressed line
    """
    cdef:
        int32_t size, first_pixel, n_fields, n_restpx, len_a, len_b, cur, prev, i
        int32_t[::1] fielda, fieldb
        uint16_t position, overflow_position
    
    size = data.shape[0]
    first_pixel = data[0]
    

    #data[1:] - data[:size-1]
    #pixel_diff = numpy.empty(size-1, dtype=numpy.int32)
    prev = first_pixel
    for i in range(1, size):
        cur = data[i]
        pixel_diff[i-1] = cur - prev
        prev = cur

    position = _write_escaped(first_pixel, buffer, 0)

    n_fields = (size-1) // 16
    n_restpx = (size-1) % 16

    for i in range(n_fields):
        fielda = pixel_diff[:8]
        fieldb = pixel_diff[8:16]

        len_a = _get_fieldsize(fielda)
        len_b = _get_fieldsize(fieldb)
        buffer[position] = (len_b << 4) | len_a
        position += 1
        
        overflow_position = _compress_field(fielda, len_a, buffer, position, position+len_a+len_b)
        position = _compress_field(fieldb, len_b, buffer, position+len_a, overflow_position)

        pixel_diff = pixel_diff[16:]

    for i in range(n_restpx):
        position = _write_escaped(pixel_diff[i], buffer, position)

    return position

def compress(int32_t [:,::1] frame):
    """compress a frame using the agi_bitfield algorithm
    
    Gil-free implementation of the compression algorithm
    
    :param frame: numpy.ndarray
    :returns bytes
    """
    cdef:
        Py_ssize_t shape, index
        uint8_t[::1] buffer    # Contains the compressed lines
        uint32_t[::1] cumsum
        int32_t [::1] delta     # buffer space used by compre_row
        uint32_t current
        uint16_t size
        uint64_t one=1
        
        
    shape = frame.shape[0]
    assert frame.shape[1] == shape, "Input shape is expected to be square !"
    
    buffer = numpy.empty(8*shape*shape, numpy.uint8) #Should be able to accomodate 4096² data 
    cumsum = numpy.empty(shape, numpy.uint32)
    delta = numpy.empty(shape-1, numpy.int32)

    with nogil:
        current = 0
        for index in range(shape):
            cumsum[index] = current
            size = _compress_row(frame[index], buffer[4+current:], delta)
            current += size
        buffer[0] = current & ((one<<8)-1)
        buffer[1] = (current & ((one<<16)-1))>>8
        buffer[2] = (current & ((one<<24)-1))>>16
        buffer[3] = (current & ((one<<32)-1))>>24

    if numpy.little_endian:
        return (numpy.asarray(buffer[:current+4]).tobytes()+
                numpy.asarray(cumsum).tobytes())
    else:
        return (numpy.asarray(buffer[:current+4]).tobytes()+
                numpy.asarray(cumsum).byteswap.tobytes())
