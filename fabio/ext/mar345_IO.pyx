# coding: utf-8
#
#    Project: X-ray image reader
#             https://github.com/silx-kit/fabio
#
#    Copyright (C) 2015 European Synchrotron Radiation Facility, Grenoble, France
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
"""
New Cython version of mar345_IO for preparing the migration to Python3

Compressor & decompressor for "pack" algorithm by JPA, binding to CCP4 libraries
those libraries are re-implemented in Cython.

Known bugs:
-----------

The precomp/postdec part need to be performed operation in int16 and exports
uint16. Some calculation are overflowing, this is needed to reproduce the
original implementation which is buggy

"""

__authors__ = ["Jerome Kieffer", "Gael Goret", "Thomas Vincent"]
__contact__ = "jerome.kieffer@esrf.eu"
__license__ = "MIT"
__copyright__ = "2012-2016, European Synchrotron Radiation Facility, Grenoble, France"
__date__ = "11/08/2017"

import cython
cimport numpy as cnp

import numpy
import os
import tempfile
import logging
logger = logging.getLogger(__name__)


ctypedef fused any_int_t:
    cnp.int8_t
    cnp.int16_t
    cnp.int32_t
    cnp.int64_t

# Few constants:
cdef:
    cnp.uint8_t *CCP4_PCK_BIT_COUNT = [0, 4, 5, 6, 7, 8, 16, 32]
    cnp.uint8_t *CCP4_BITSIZE = [0, 0, 0, 0, 1, 2, 3, 4, 5, 0, 0, 0, 0, 0, 0, 0,
                                 6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7]
    int CCP4_PCK_BLOCK_HEADER_LENGTH = 6


cdef extern from "ccp4_pack.h":
    void* mar345_read_data_string(char *instream, int ocount, int dim1, int dim2) nogil
    void pack_wordimage_c(short int*, int , int , char*) nogil
    void* ccp4_unpack_string   (void *, void *, size_t, size_t, size_t) nogil
    void* ccp4_unpack_v2_string(void *, void *, size_t, size_t, size_t) nogil
cdef int PACK_SIZE_HIGH = 8


@cython.boundscheck(False)
def compress_pck(image not None, bint use_CCP4=False):
    """
    :param image: numpy array as input
    :param use_CCP4: use the former LGPL implementation provided by CCP4
    :return: binary stream
    """
    cdef:
        cnp.uint32_t  size, dim0, dim1, i, j
        int fd, ret
        char* name
        cnp.int16_t[::1] data
        cnp.int32_t[::1] raw
        bytes output

    assert image.ndim == 2, "Input image shape is 2D"
    size = image.size
    dim0 = image.shape[0]
    dim1 = image.shape[1]
    data = numpy.ascontiguousarray(image.ravel(), dtype=numpy.int16)
    if use_CCP4:
        (fd, fname) = tempfile.mkstemp()
        fname = fname.encode("ASCII")
        name = <char*> fname
        with nogil:
            pack_wordimage_c(<short int *> &data[0], dim1, dim0, name)
        with open(name, "rb") as f:
            f.seek(0)
            output = f.read()
        os.close(fd)
        os.unlink(fname)
    else:
        output = ("\nCCP4 packed image, X: %04d, Y: %04d\n" % (dim1, dim0)).encode("ASCII")
        raw = precomp(data, dim1)
        cont = pack_image(raw, False)
        output += cont.get().tostring()
    return output


@cython.boundscheck(False)
@cython.cdivision(True)
def uncompress_pck(bytes raw not None, dim1=None, dim2=None, overflowPix=None, version=None, normal_start=None, swap_needed=None, bint use_CCP4=False):
    """
    Unpack a mar345 compressed image

    :param raw: input string (bytes in python3)
    :param dim1,dim2: optional parameters size
    :param overflowPix: optional parameters: number of overflowed pixels
    :param version: PCK version 1 or 2
    :param normal_start: position of the normal value section (can be auto-guessed)
    :param swap_needed: set to True when reading data from a foreign endianness (little on big or big on little)
    :return: ndarray of 2D with the right size
    """
    cdef:
        int cdimx, cdimy, chigh, cversion, records, normal_offset, lenkey, i, stop, idx, value
        cnp.uint32_t[:, ::1] data
        cnp.uint8_t[::1] instream
        cnp.int32_t[::1] unpacked
        cnp.int32_t[:, ::1] overflow_data  # handles overflows
        void* out
    end = None
    key1 = b"CCP4 packed image, X: "
    key2 = b"CCP4 packed image V2, X: "

    if (dim1 is None) or (dim2 is None) or \
       (version not in [1, 2]) or \
       (version is None) or \
       (normal_start is None):
        start = raw.find(key2)
        key = key2
        cversion = 2
        if start == -1:
            start = raw.find(key1)
            key = key1
            cversion = 1
        lenkey = len(key)
        start = raw.index(key) + lenkey
        sizes = raw[start:start + 13]
        cdimx = < int > int(sizes[:4])
        cdimy = < int > int(sizes[-4:])
        normal_offset = start + 13
    else:
        cdimx = < int > dim1
        cdimy = < int > dim2
        cversion = <int> version
        normal_offset = <int> normal_start
        if cversion == 1:
            lenkey = len(key1)
        else:
            lenkey = len(key2)
    if cversion not in [1, 2]:
        raise RuntimeError("Cannot determine the compression scheme for PCK compression (either version 1 or 2)")
    if (overflowPix is None) and (overflowPix is not False):
        end = raw.find("END OF HEADER")
        start = raw[:end].find("HIGH")
        hiLine = raw[start:end]
        hiLine = hiLine.split("\n")[0]
        word = hiLine.split()
        if len(word) > 1:
            chigh = int(word[1])
        else:
            logger.warning("Error while looking for overflowed pixels in line %s", hiLine.strip())
            chigh = 0
    else:
        chigh = < int > overflowPix

    instream = numpy.fromstring(raw[normal_offset:].lstrip(), dtype=numpy.uint8)

    if use_CCP4:
        data = numpy.empty((cdimy, cdimx), dtype=numpy.uint32)
        with nogil:
            ################################################################################
            #      rely to whichever version of ccp4_unpack is appropriate
            ################################################################################
            if cversion == 1:
                ccp4_unpack_string(&data[0, 0], &instream[0], cdimx, cdimy, 0)
            else:
                # cversion == 2:
                ccp4_unpack_v2_string(&data[0, 0], &instream[0], cdimx, cdimy, 0)
    else:
        # There is a bug in the mar345 implementation which performs arithmetics
        # of post-decompression in 16bits integers and overflows with large values
        unpacked = unpack_pck(instream, cdimx, cdimy).get1d()
        data = numpy.ascontiguousarray(postdec(unpacked, cdimx), numpy.uint32).reshape((cdimy, cdimx))

    if chigh > 0:
        ################################################################################
        # handle overflows: Each record is 8 overflow of 2x32bits integers
        ################################################################################
        records = (chigh + PACK_SIZE_HIGH - 1) // PACK_SIZE_HIGH
        stop = normal_offset - lenkey - 14
        odata = numpy.fromstring(raw[stop - 64 * records: stop], dtype=numpy.int32)
        if swap_needed:
            odata.byteswap(True)
        overflow_data = odata.reshape((-1, 2))
        for i in range(overflow_data.shape[0]):
            idx = overflow_data[i, 0] - 1     # indexes are even values (-1 because 1 based counting)
            value = overflow_data[i, 1]  # values are odd values
            if (idx >= 0) and (idx < cdimx * cdimy):
                data[idx // cdimx, idx % cdimx] = <cnp.uint32_t> value
    return numpy.asarray(data)


################################################################################
# Re-Implementation of the pck compression/decompression
################################################################################

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
@cython.initializedcheck(False)
cpdef inline cnp.int32_t[::1] precomp(cnp.int16_t[::1] img, cnp.uint32_t width):
    """Pre-compression by subtracting the average value of the four neighbours

    Actually it looks a bit more complicated:

    * there comes the +2 from ?
    * the first element remains untouched
    * elements of the first line (+ first of second) use only former element


    JPA, the original author wrote:
    Compression is achieved by first calculating the differences between every
    pixel and the truncated value of four of its neighbours. For example:
    the difference for a pixel at img[x, y] is:

    comp[y, x] =  img[y, x] - (img[y-1, x-1] + img[y-1, x] + img[y-1, x+1] + img[y, x-1]) / 4

    This part implements overlows of int16 as the reference implementation is buggy
    """
    cdef:
        cnp.uint32_t size, i
        cnp.int32_t[::1] comp
        cnp.int16_t last, cur, im0, im1, im2
    size = img.size
    comp = numpy.zeros(size, dtype=numpy.int32)

    with nogil:
        # First pixel
        comp[0] = last = im0 = img[0]
        im1 = img[1]
        im2 = img[2]

        # First line (+ 1 pixel)
        for i in range(1, width + 1):
            cur = img[i]
            comp[i] = cur - last
            last = cur

        # Rest of the image
        for i in range(width + 1, size):
            cur = img[i]
            comp[i] = <cnp.int16_t> (cur - (last + im0 + im1 + im2 + 2) // 4)
            last = cur
            im0 = im1
            im1 = im2
            im2 = img[i - width + 2]

    return comp


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
@cython.initializedcheck(False)
cpdef inline cnp.uint32_t[::1] postdec(cnp.int32_t[::1] comp, int width):
    """Post decompression by adding the average value of the four neighbours

    Actually it looks a bit more complicated:

    * there comes the +2 from ?
    * the first element remains untouched
    * elements of the first line (+ fist of second) use only former element

    JPA, the original author wrote:
    Compression is achieved by first calculating the differences between every
    pixel and the truncated value of four of its neighbours. For example:
    the difference for a pixel at img[x, y] is:

    comp[y, x] =  img[y, x] - (img[y-1, x-1] + img[y-1, x] + img[y-1, x+1] + img[y, x-1]) / 4

    This part implementes overlows of int16 as the reference implementation is bugged
    """
    cdef:
        cnp.uint32_t size, i
        cnp.uint32_t[::1] img
        cnp.int16_t last, cur, fl0, fl1, fl2
    size = comp.size

    img = numpy.zeros(size, dtype=numpy.uint32)

    with nogil:

        # First pixel
        last = comp[0]
        img[0] = last

        # First line (+ 1 pixel)
        for i in range(1, width + 1):
            img[i] = cur = comp[i] + last
            last = cur

        # Rest of the image: not parallel in this case
        fl0 = img[0]
        fl1 = img[1]
        fl2 = img[2]
        for i in range(width + 1, size):
            # overflow expected here.
            cur = comp[i] + (last + fl0 + fl1 + fl2 + 2) // 4
            # ensures the data is cropped at 16 bits!
            img[i] = <cnp.uint16_t> cur
            last = cur
            fl0 = fl1
            fl1 = fl2
            fl2 = img[i - width + 2]

    return img


################################################################################
# Re-Implementation of the pck compression stuff
################################################################################


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
@cython.initializedcheck(False)
cpdef inline int calc_nb_bits(any_int_t[::1] data, cnp.uint32_t start, cnp.uint32_t stop) nogil:
    """Calculate the number of bits needed to encode the data

    :param data: input data, probably slices of a larger array
    :param start: start position
    :param stop: stop position
    :return: the needed number of bits to store the values

    Comment from JPA:
    .................

    Returns the number of bits necessary to encode the longword-array 'chunk'
    of size 'n' The size in bits of one encoded element can be 0, 4, 5, 6, 7,
    8, 16 or 32.
     """
    cdef:
        cnp.uint32_t size, maxsize, i, abs_data
        any_int_t read_data

    size = stop - start
    maxsize = 0
    for i in range(start, stop):
        read_data = data[i]
        abs_data = - read_data if read_data < 0 else read_data
        if abs_data > maxsize:
            maxsize = abs_data
    if maxsize == 0:
        return 0
    elif maxsize < 8:
        return size * 4
    elif maxsize < 16:
        return size * 5
    elif maxsize < 32:
        return size * 6
    elif maxsize < 64:
        return size * 7
    elif maxsize < 128:
        return size * 8
    elif maxsize < 32768:
        return size * 16
    else:
        return size * 32


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
@cython.initializedcheck(False)
def pack_image(img, bint do_precomp=True):
    """Pack an image into a binary compressed block

    :param img: input image as numpy.int16
    :param do_precomp: perform the subtraction to the 4 neighbours's average. False is for testing the packing only
    :return: 1D array of numpy.int8

    JPA wrote:
    ..........
    Pack image 'img', containing 'x * y' WORD-sized pixels into byte-stream
    """
    cdef:
        cnp.uint32_t nrow, ncol, size, stream_size
        cnp.int16_t[::1] input_image
        cnp.int32_t[::1] raw
        PackContainer container
        cnp.uint32_t i, position
        cnp.uint32_t nb_val_packed
        cnp.uint32_t current_block_size, next_bock_size

    if do_precomp:
        assert len(img.shape) == 2
        nrow = img.shape[0]
        ncol = img.shape[1]
        input_image = numpy.ascontiguousarray(img, dtype=numpy.int16).ravel()
        # pre compression: subtract the average of the 4 neighbours
        raw = precomp(input_image, ncol)
        size = nrow * ncol
    else:
        raw = numpy.ascontiguousarray(img, dtype=numpy.int32).ravel()
        size = raw.size

    # allocation of the output buffer
    container = PackContainer(size)

    position = 0
    while position < size:
        nb_val_packed = 1
        current_block_size = calc_nb_bits(raw, position, position + nb_val_packed)
        while ((position + nb_val_packed) < size) and (nb_val_packed < 128):
            if (position + 2 * nb_val_packed) < size:
                next_bock_size = calc_nb_bits(raw, position + nb_val_packed, position + 2 * nb_val_packed)
            else:
                break
            if 2 * max(current_block_size, next_bock_size) < (current_block_size + next_bock_size + CCP4_PCK_BLOCK_HEADER_LENGTH):
                nb_val_packed *= 2
                current_block_size = 2 * max(current_block_size, next_bock_size)
            else:
                break
        container.append(raw, position, nb_val_packed, current_block_size)
        position += nb_val_packed

    return container


cdef class PackContainer:
    cdef:
        readonly cnp.uint32_t position, offset, allocated
        cnp.uint8_t[::1] data

    def __cinit__(self, cnp.uint32_t size=4096):
        """Constructor of the class

        :param size: start size of the array
        """
        self.position = 0
        self.offset = 0
        self.allocated = size
        self.data = numpy.zeros(self.allocated, dtype=numpy.uint8)

    def __dealloc__(self):
        self.data = None

    def get(self):
        """retrieve the populated array"""
        if self.offset:
            end = self.position + 1
        else:
            end = self.position
        return numpy.asarray(self.data[:end])

    @cython.boundscheck(False)
    @cython.wraparound(False)
    @cython.cdivision(True)
    @cython.initializedcheck(False)
    cpdef append(self, cnp.int32_t[::1] data, cnp.uint32_t position, cnp.uint32_t nb_val, cnp.uint32_t block_size):
        """Append a block of data[position: position+nb_val] to the compressed
        stream. Only the most significant bits are takes.

        :param data: input uncompressed image as 1D array
        :param position: start position of reading of the image
        :param nb_val: number of value from data to pack in the block
        :param block_size: number of bits for the whole block

        The 6 bits header is managed here as well as the stream resizing.
        """
        cdef:
            cnp.uint32_t offset, index, i, bit_per_val, nb_bytes
            cnp.uint64_t tmp, tostore, mask
            cnp.int64_t topack

        bit_per_val = block_size // nb_val

        # realloc memory if needed
        nb_bytes = (CCP4_PCK_BLOCK_HEADER_LENGTH + block_size + 7) // 8
        if self.position + nb_bytes >= self.allocated:
            self.allocated *= 2
            new_stream = numpy.zeros(self.allocated, dtype=numpy.uint8)
            if self.offset:
                new_stream[:self.position + 1] = self.data[:self.position + 1]
            else:
                new_stream[:self.position] = self.data[:self.position]
            self.data = new_stream

        with nogil:
            if self.offset == 0:
                tmp = 0
            else:
                tmp = self.data[self.position]

            # append 6 bits of header
            tmp |= pack_nb_val(nb_val, bit_per_val) << self.offset
            self.offset += CCP4_PCK_BLOCK_HEADER_LENGTH
            self.data[self.position] = tmp & (255)
            if self.offset >= 8:
                self.position += 1
                self.offset -= 8
                self.data[self.position] = (tmp >> 8) & (255)

            # now pack every value in input stream"
            for i in range(nb_val):
                topack = data[position + i]

                mask = ((1 << (bit_per_val - 1)) - 1)
                tmp = (topack & mask)
                if topack < 0:
                    # handle the sign
                    tmp |= 1 << (bit_per_val - 1)

                # read last position
                if self.offset == 0:
                    tostore = 0
                else:
                    tostore = self.data[self.position]

                tostore |= tmp << self.offset
                self.offset += bit_per_val

                # Update the array
                self.data[self.position] = tostore & (255)
                while self.offset >= 8:
                    tostore = tostore >> 8
                    self.offset -= 8
                    self.position += 1
                    self.data[self.position] = tostore & (255)


cpdef inline cnp.uint8_t pack_nb_val(cnp.uint8_t nb_val, cnp.uint8_t value_size) nogil:
    """Calculate the header to be stored in 6 bits

    :param nb_val: number of values to be stored: must be a power of 2 <=128
    :param value_size: can be 0, 4, 5, 6, 7, 8, 16 or 32, the number of bits per value
    :return: the header as an unsigned char
    """
    cdef:
        cnp.uint32_t value, i

    value = 0
    for i in range(8):
        if (nb_val >> i) == 1:
            value |= i
            break
    value |= (CCP4_BITSIZE[value_size]) << (CCP4_PCK_BLOCK_HEADER_LENGTH >> 1)
    # should be 6/2 = 3
    return value


################################################################################
# Re-Implementation of the pck uncompression stuff
################################################################################
@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
@cython.initializedcheck(False)
cpdef UnpackContainer unpack_pck(cnp.uint8_t[::1] stream, int ncol, int nrow):
    """Unpack the raw stream and return the image
    V1 only for now, V2 may be added later

    :param stream: raw input stream
    :param ncol: number of columns in the image (i.e width)
    :param nrow: number if rows in the image (i.e. height)
    :return: Container with decompressed image
    """
    cdef:
        cnp.uint32_t offset        # Number of bit to offset in the current byte
        cnp.uint32_t pos, end_pos  # current position and last position of block  in byte stream
        cnp.uint32_t size          # size of the input stream
        cnp.int32_t value, next    # integer values
        cnp.uint32_t nb_val_packed, nb_bit_per_val, nb_bit_in_block
        UnpackContainer cont       # Container with unpacked data

    cont = UnpackContainer(ncol, nrow)
    size = stream.size

    # Luckily we start at byte boundary
    offset = 0
    pos = 0

    while pos < (size) and cont.position < (cont.size):
        value = stream[pos]
        if offset > (8 - CCP4_PCK_BLOCK_HEADER_LENGTH):
            # wrap around
            pos += 1
            next = stream[pos]
            value |= next << 8
            value = value >> offset
            offset += CCP4_PCK_BLOCK_HEADER_LENGTH - 8
        elif offset == (8 - CCP4_PCK_BLOCK_HEADER_LENGTH):
            # Exactly on the boundary
            value = value >> offset
            pos += 1
            offset = 0
        else:
            # stay in same byte
            value = value >> offset
            offset += CCP4_PCK_BLOCK_HEADER_LENGTH

        # we use 7 as mask: decimal value of 111

        # move from offset, read 3 lsb, take the power of 2
        nb_val_packed = 1 << (value & 7)
        # read 3 next bits, search in LUT for the size of each element in block
        nb_bit_per_val = CCP4_PCK_BIT_COUNT[(value >> 3) & 7]

        if nb_bit_per_val == 0:
            cont.set_zero(nb_val_packed)
        else:
            nb_bit_in_block = nb_bit_per_val * nb_val_packed
            cont.unpack(stream, pos, offset, nb_val_packed, nb_bit_per_val)
            offset += nb_bit_in_block
            pos += offset // 8
            offset %= 8
    return cont


cdef class UnpackContainer:
    cdef:
        readonly cnp.uint32_t nrow, ncol, position, size
        readonly cnp.int32_t[::1] data
        # readonly list debug

    def __cinit__(self, int ncol, int nrow):
        self.nrow = nrow
        self.ncol = ncol
        self.size = nrow * ncol
        self.data = numpy.zeros(self.size, dtype=numpy.int32)
        self.position = 0

    def __dealloc__(self):
        self.data = None

    def get(self):
        """retrieve the populated array"""
        return numpy.asarray(self.data).reshape((self.nrow, self.ncol))

    cpdef cnp.int32_t[::1] get1d(self):
        """retrieve the populated array"""
        return self.data

    cpdef set_zero(self, int number):
        "set so many zeros"
        self.position += number

    @cython.boundscheck(False)
    @cython.wraparound(False)
    @cython.cdivision(True)
    @cython.initializedcheck(False)
    cpdef unpack(self, cnp.uint8_t[::1] stream, cnp.uint32_t pos, cnp.uint32_t offset, cnp.uint32_t nb_value, cnp.uint32_t value_size):
        """unpack a block on data, all the same size

        :param stream: input stream, already sliced
        :param offset: number of bits of offset, at the begining of the stream
        :param nb_value: number of values to unpack
        :param value_size: number of bits of each value
        """
        cdef:
            cnp.uint32_t i, j        # simple counters
            cnp.uint32_t new_offset  # position after read
            cnp.int64_t cur, tmp2    # value to be stored
            cnp.uint64_t tmp         # under contruction: needs to be unsigned
            int to_read              # number of bytes to read

        with nogil:
            cur = 0
            for i in range(nb_value):

                # read as many bytes as needed and unpack them to tmp variable

                tmp = stream[pos] >> offset

                new_offset = value_size + offset
                to_read = (new_offset + 7) // 8

                for j in range(1, to_read):
                    tmp |= (stream[pos + j]) << (8 * j - offset)

                # Remove the msb of tmp to keep only the interesting values
                cur = tmp & ((1 << (value_size)) - 1)

                # change sign if most significant bit is 1
                if cur >> (value_size - 1):
                    cur |= (-1) << (value_size - 1)

                # Update the storage
                self.data[self.position] = cur
                self.position += 1

                # Update the position in the array
                pos = pos + new_offset // 8
                offset = new_offset % 8
