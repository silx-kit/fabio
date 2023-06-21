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
#  Permission is hereby granted, free of charge, to any person
#  obtaining a copy of this software and associated documentation files
#  (the "Software"), to deal in the Software without restriction,
#  including without limitation the rights to use, copy, modify, merge,
#  publish, distribute, sublicense, and/or sell copies of the Software,
#  and to permit persons to whom the Software is furnished to do so,
#  subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be
#  included in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
#  OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#  NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#  HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
#  WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#  OTHER DEALINGS IN THE SOFTWARE.

"""Compression and decompression algorithm for Esperanto format

Authors: Jérôme Kieffer, ESRF email:jerome.kieffer@esrf.fr
         Florian Plaswig

Inspired by C++ code:   https://git.3lp.cx/dyadkin/cryio/src/branch/master/src/esperantoframe.cpp
        Fortran code:   https://svn.debroglie.net/debroglie/Oxford/trunk/diamond2crysalis/bitfield.F90
"""
__author__ = ["Florian Plaswig", "Jérôme Kieffer"]
__contact__ = "jerome.kieffer@esrf.eu"
__license__ = "MIT"
__date__ = "13/11/2020"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"

import logging
from io import BytesIO
from struct import pack, unpack as unpack_
try:
    from ..ext._agi_bitfield import get_fieldsize as _get_fieldsize, compress_row as _compress_row, compress as _compress
except ImportError:
    _get_fieldsize = None
    _compress_row = None
    _compress = None
logger = logging.getLogger(__name__)
import numpy

unpack = lambda fmt, buff: unpack_(fmt, buff)[0]

MASK = [(1 << i) - 1 for i in range(9)]


def compress(frame):
    """compress a frame using the agi_bitfield algorithm
    :param frame: numpy.ndarray
    :returns bytes
    """

    dim = frame.shape
    buffer = BytesIO()

    row_start = numpy.zeros(dim[0], dtype=numpy.uint32)

    for row_index in range(0, dim[0]):
        row_start[row_index] = buffer.tell()
        _compress_row(frame[row_index], buffer)

    data_size = pack("<I", buffer.tell())

    if numpy.little_endian:
        buffer.write(row_start.tobytes())
    else:
        buffer.write(row_start.byteswap.tobytes())

    return data_size + buffer.getvalue()


def compress_row(data, buffer):
    """compress a single row
    :arg data numpy.array
    :arg buffer io.BytesIO
    """

    first_pixel = data[0]
    pixel_diff = data[1:] - data[:-1]

    write_escaped(first_pixel, buffer)

    n_fields = len(pixel_diff) // 16
    n_restpx = len(pixel_diff) % 16

    for _ in range(0, n_fields):
        fielda = pixel_diff[:8]
        fieldb = pixel_diff[8:16]

        len_a = _get_fieldsize(fielda)
        len_b = _get_fieldsize(fieldb)
        len_byte = (len_b << 4) | len_a
        buffer.write(pack("B", len_byte))

        of_buff = BytesIO()
        compressed_fielda = compress_field(fielda, len_a, of_buff)
        compressed_fieldb = compress_field(fieldb, len_b, of_buff)

        buffer.write(compressed_fielda + compressed_fieldb + of_buff.getvalue())

        pixel_diff = pixel_diff[16:]

    for restpx in range(0, n_restpx):
        write_escaped(pixel_diff[restpx], buffer)


if _compress_row is None:
    _compress_row = compress_row


def decompress(comp_frame, dimensions):
    """decompresses a frame that was compressed using the agi_bitfield algorithm
    :param comp_frame: bytes
    :param dimensions: tuple
    :return numpy.ndarray
    """

    row_count, col_count = dimensions

    # read data components (row indices are ignored)
    data_size = unpack("I", comp_frame[:4])
    data_block = BytesIO(comp_frame[4:])
    logger.debug("Size of binary data block: %d with image size: %s, compression ratio: %.3fx", data_size, dimensions, 4 * row_count * col_count / data_size)
    output = numpy.zeros(dimensions, dtype=numpy.int32)

    for row_index in range(row_count):
        output[row_index] = decompress_row(data_block, col_count)

    return output.cumsum(axis=1)


def decompress_row(buffer, row_length):
    """decompress a single row
    :param buffer: io.BytesIO
    :param row_length: int
    :returns list
    """

    first_pixel = read_escaped(buffer)

    n_fields = (row_length - 1) // 16
    n_restpx = (row_length - 1) % 16

    pixels = [first_pixel]
    for field in range(n_fields):
        lb = unpack("B", buffer.read(1))
        len_b, len_a = read_len_byte(lb)

        field_a = decode_field(buffer.read(len_a))
        field_b = decode_field(buffer.read(len_b))

        undo_escapes(field_a, len_a, buffer)
        undo_escapes(field_b, len_b, buffer)

        pixels += field_a
        pixels += field_b

    pixels += [read_escaped(buffer) for _ in range(n_restpx)]

    return pixels


def fortran_fieldsize(nbvalue):
    "Direct translation of Fortran"
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


def get_fieldsize(array):
    """determine the fieldsize to store the given values
    :param array numpy.array
    :returns int
    """
    return max(fortran_fieldsize(array.max()), fortran_fieldsize(array.min()))


if _get_fieldsize is None:
    _get_fieldsize = get_fieldsize


def compress_field(ifield, fieldsize, overflow_table):
    """compress a field with given size
    :param ifield: numpy.ndarray
    :param fieldsize: int
    :param overflow_table: io.BytesIO
    :returns int
    """
    if fieldsize == 8:
        # we have to deal offsets but not bitshifts
        conv_ = MASK[fieldsize - 1]
        tmp = bytearray(8)
        for i, elem in enumerate(ifield):
            if -127 <= elem < 127:
                tmp[i] = elem + conv_
            elif -32767 <= elem < 32767:
                tmp[i] = 254
                overflow_table.write(pack("<h", elem))
            else:
                tmp[i] = 255
                overflow_table.write(pack("<i", elem))
        return bytes(tmp)
    elif fieldsize > 0:
        # we have to deal with bit-shifts but not offsets
        conv_ = MASK[fieldsize - 1]
        compressed_field = 0
        for i, elem in enumerate(ifield):
            val = int(elem) + conv_
            compressed_field |= val << (i * fieldsize)
        try:
            res = pack("<Q", compressed_field)
        except:
            logger.error("Exception in struct.pack: %s %s %s %s", fieldsize, type(fieldsize), ifield, compressed_field)
            raise
        return res[:fieldsize]
    else:
        raise AssertionError("fieldsize is between 0 and 8")


def decode_field(field):
    """decodes a field from bytes. 
    
    One field always encode for 8 pixels but my be stored on 1 to 8 pixels 
    (overflow are handeled separately)
    
    :param field: bytes
    :returns list
    """
    size = len(field)
    if size == 8:
        return list(unpack_("B"*8, field))
    elif size < 8:
        field = unpack("<Q", field.ljust(8, b'\x00'))
        mask_ = MASK[size]
        return [(field >> (size * i)) & mask_ for i in range(8)]
    else:
        raise RuntimeError("Expected a maximum of 8 bytes, got %s" % size)


def read_len_byte(lb):
    """parses the length byte and returns the sizes of the next twofields
    :param lb: int/byte
    :returns tuple
    """
    return lb >> 4, lb & 0xf


def write_escaped(value, buffer):
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


def read_escaped(buffer):
    """reads byte value that might be escaped from a buffer
    :param buffer: io.BytesIO
    :returns int
    """
    byte = buffer.read(1)
    if byte == b'\xfe':  # two byte overflow
        return unpack("<h", buffer.read(2))
    elif byte == b'\xff':  # four byte overflow
        return unpack("<i", buffer.read(4))
    else:  # no overflow
        return unpack("B", byte) - 127


def undo_escapes(field, length, buffer):
    """undo escaping of values in a field
    :param field: list
    :param length: int
    :param buffer: io.BytesIO
    """
    conv_ = MASK[length - 1]
    for i, val in enumerate(field):
        if val == 0xfe:
            field[i] = unpack("<h", buffer.read(2))
        elif val == 0xff:
            field[i] = unpack("<i", buffer.read(4))
        else:
            field[i] = val - conv_
