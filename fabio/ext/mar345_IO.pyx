# coding: utf-8
#
#    Project: X-ray image reader
#             https://github.com/kif/fabio
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
New Cython version of mar345_io for preparing the migration to Python3

Compressor & decompressor for "pack" algorithm by JPA, binding to CCP4 libraries

Warning: decompressor is just a cython porting of mar345_io, but in cython so (soon) python3 compliant.

Future: make those algorithm actually generate strings not go via files;
        it will allow a broader use of the algorithm.

"""

__authors__ = ["Jerome Kieffer", "Gael Goret"]
__contact__ = "jerome.kieffer@esrf.eu"
__license__ = "MIT"
__copyright__ = "2012-2015, European Synchrotron Radiation Facility, Grenoble, France"
__date__ = "07/09/2016" 

import cython
cimport numpy as cnp

from cython.parallel import prange

import numpy
import os
import tempfile

cdef cnp.uint8_t[:] CCP4_PCK_BIT_COUNT = numpy.array([0, 4, 5, 6, 7, 8, 16, 32], dtype=numpy.uint8)
cdef int CCP4_PCK_BLOCK_HEADER_LENGTH = 6
#cdef cnp.uint8_t[:]  CCP4_PCK_MASK = numpy.array([0, 1, 3, 7, 15, 31, 63, 127, 255], dtype=numpy.uint8)

cdef extern from "ccp4_pack.h":
    void* mar345_read_data_string(char *instream, int ocount, int dim1, int dim2) nogil
    void pack_wordimage_c(short int*, int , int , char*) nogil
    void* ccp4_unpack_string   (void *, void *, size_t, size_t, size_t) nogil
    void* ccp4_unpack_v2_string(void *, void *, size_t, size_t, size_t) nogil
cdef int PACK_SIZE_HIGH = 8


@cython.boundscheck(False)
def compress_pck(inputArray not None):
    """
    @param inputArray: numpy array as input
    @param filename: file to write data to
    """
    cdef:
        long  size = inputArray.size
        int dim0, dim1, i, j, fd, ret
        char* name
        cnp.uint16_t[:] data
    assert inputArray.ndim == 2, "shape is 2D"
    dim0 = inputArray.shape[0]
    dim1 = inputArray.shape[1]
    data = numpy.ascontiguousarray(inputArray.astype(numpy.uint16).ravel(), dtype=numpy.uint16)

    (fd, fname) = tempfile.mkstemp()
    fname = fname.encode("ASCII")
    name = <char*> fname
    with nogil:
        pack_wordimage_c(< short int *> &data[0], dim1, dim0, name)
    with open(name, "rb") as f:
        f.seek(0)
        output = f.read()
    os.close(fd)
    os.unlink(fname)
    return output


@cython.boundscheck(False)
@cython.cdivision(True)
def uncompress_pck(bytes raw not None, dim1=None, dim2=None, overflowPix=None, version=None, normal_start=None, swap_needed=None):
    """
    Unpack a mar345 compressed image

    @param raw: input string (bytes in python3)
    @param dim1,dim2: optional parameters size
    @param overflowPix: optional parameters: number of overflowed pixels
    @param version: PCK version 1 or 2
    @param normal_start: position of the normal value section (can be auto-guessed)
    @param swap_needed: set to True when reading data from a foreign endianness (little on big or big on little)
    @return : ndarray of 2D with the right size
    """
    cdef:
        int cdimx, cdimy, chigh, cversion, records, normal_offset, lenkey, i, stop, idx, value
        cnp.uint32_t[:, :] data
        cnp.uint8_t[:] instream
        cnp.int32_t[:, :] overflow_data  # handles overflows
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
    if (overflowPix is None):
        end = raw.find("END OF HEADER")
        start = raw[:end].find("HIGH")
        hiLine = raw[start:end]
        hiLine = hiLine.split("\n")[0]
        word = hiLine.split()
        if len(word) > 1:
            chigh = int(word[1])
        else:
            print("Error while looking for overflowed pixels in line %s" % hiLine.strip())
            chigh = 0
    else:
        chigh = < int > overflowPix
    data = numpy.empty((cdimy, cdimx), dtype=numpy.uint32)   
    instream = numpy.fromstring(raw[normal_offset:].lstrip(), dtype=numpy.uint8)
    with nogil:
        ################################################################################
        #      rely to whichever version of ccp4_unpack is appropriate
        ################################################################################
        if cversion == 1:
            ccp4_unpack_string(&data[0,0], &instream[0], cdimx, cdimy, 0)
        else:
            # cversion == 2:
            ccp4_unpack_v2_string(&data[0,0], &instream[0], cdimx, cdimy, 0)

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
#         valid_sum = valid.sum()
#         valid_idx = numpy.where(valid)[0]
#         if valid_sum > chigh:
#             print("Found %s High values, expected only %s. Taking the last ones (mar555 compatibility)" % (valid.sum, chigh))
#             valid_idx = numpy.where(valid)[0][valid_sum - chigh:]
#             idx = idx.take(valid_idx)
#             value = value.take(valid_idx)
#         else:
#             idx = idx[valid]
#             value = value[valid]
#         data.flat[idx] = value.astype(numpy.uint32)
    return numpy.asarray(data)

################################################################################
# Re-Implementation of the pck compression 
################################################################################

cpdef cnp.int16_t[:] precomp(cnp.int16_t[:] img, int width):
    """Pre-compression by subtracting the average value of the four neighbours
    
    Actually it looks a bit more complicated:
    
    * there comes the +2 from ?
    * the first element remains untouched
    * elements of the first line (+ fist of second) use only former element  

    
    JPA, the original author wrote:
    Compression is achieved by first calculating the differences between every
    pixel and the truncated value of four of its neighbours. For example:
    the difference for a pixel at img[x, y] is:

    comp[y, x] =  img[y, x] - (img[y-1, x-1] + img[y-1, x] + img[y-1, x+1] + img[y, x-1]) / 4
    """
    cdef: 
        int size, i
        cnp.int16_t[:] comp
        cnp.int16_t last, cur
    size = img.size
    comp = numpy.zeros_like(img)
    
    # First pixel
    comp[0] = last = img[0]
    
    # First line (+ 1 pixel)
    for i in range(1, width + 1):
        cur = img[i]
        comp[i] = cur - last
        last = cur
    
    # Rest of the image
    for i in prange(width + 1, size, nogil=True):
        comp[i] += img[i] - (img[i - 1] + img[i - width + 1] + img[i - width] + img[i - width - 1] + 2) // 4

    return comp

cpdef cnp.int16_t[:] postdec(cnp.int16_t[:] comp, int width):
    """Post decompression by adding the average value of the four neighbours
    
    Actually it looks a bit more complicated:
    
    * there comes the +2 from ?
    * the first element remains untouched
    * elements of the first line (+ fist of second) use only former element  
    
    JPA , the original author wrote:
    Compression is achieved by first calculating the differences between every
    pixel and the truncated value of four of its neighbours. For example:
    the difference for a pixel at img[x, y] is:

    comp[y, x] =  img[y, x] - (img[y-1, x-1] + img[y-1, x] + img[y-1, x+1] + img[y, x-1]) / 4
    """
    cdef: 
        int size, i
        cnp.int16_t[:] img
        cnp.int16_t last, cur, fl0, fl1, fl2
    size = comp.size
    img = numpy.zeros_like(comp)
    
    # First pixel
    img[0] = last = comp[0] 
    
    # First line (+ 1 pixel)
    for i in range(1, width + 1):
        img[i] = cur = comp[i] + last  
        last = cur
    
    # Rest of the image: not paralle in this case
    fl0 = img[0]
    fl1 = img[1]
    fl2 = img[2]
    for i in range(width + 1, size):
        img[i] = cur = comp[i] + (last + fl0 + fl1 + fl2 + 2) // 4
        last = cur
        fl0 = fl1
        fl1 = fl2
        fl2 = img[i - width + 2]

    return img
 
    
cpdef int calc_nb_bits(cnp.int32_t[:] data):
    """Calculate the number of bits needed to encode the data
    
    :param data: input data, probably slices of a larger array
    :return: the needed number of bits to store the values
    
    Comment from JPA:
    .................
    
    Returns the number of bits necessary to encode the longword-array 'chunk'
    of size 'n' The size in bits of one encoded element can be 0, 4, 5, 6, 7,
    8, 16 or 32.
     """ 
    cdef int size, maxsize, i
    
    size = data.size
    maxsize = 0
    for i in range(size):
        maxsize = max(maxsize, abs(data[i]))
    if maxsize == 0:
        size = 0
    elif maxsize < 8:
        size *= 4
    elif maxsize < 16:
        size *= 5
    elif maxsize < 32:
        size *= 6
    elif maxsize < 64:
        size *= 7
    elif maxsize < 128:
        size *= 8
    elif maxsize < 32768:
        size *= 16
    else:
        size *= 32
    return size

cdef class UnpackContainer:
    cdef:
        readonly int nrow, ncol, position, size
        cnp.int16_t[:] data 
    
    def __cinit__(self, int ncol, int nrow):
        self.nrow = nrow
        self.ncol = ncol
        self.size = nrow * ncol
        self.data = numpy.zeros(self.size, dtype=numpy.int16)
        self.position = 0
    
    def __dealloc__(self):
        self.data = None
        
    cpdef get(self):
        """retrieve the populated array"""
        return numpy.asarray(self.data).reshape((self.ncol, self.nrow))
    
    cpdef set_zero(self, int number):
        "set so many zeros"
        self.position += number
    
    cpdef unpack(self, cnp.uint8_t[:] stream, int offset, int nb_value, int value_size):
        """unpack a block on data, all the same size
        
        :param stream: input stream, already sliced
        :param offset: number of bits of offset, at the begining of the stream 
        :param nb_value: number of values to unpack
        :param value_size: number of bits of each value
        """
        cdef:
            int i, j       # simple counters
            int value, tmp # value to be stored, under contruction
            int pos        # position in stream
            int to_read    # number of bytes to read
        value = 0
        pos = 0
        for i in range(nb_value):
            tmp = 0
            # read as many bytes as needed and unpack them to tmp variable
            to_read = (value_size - offset + 7) % 8
            for j in range(to_read + 1):
                tmp |= (stream[pos + j]) << (8 * j)
            # Remove the lsb of tmp up to offset and apply the mask 
            cur = (tmp >> offset) & ((1 << value_size) - 1)

            # change sign if most significant bit is 1
            if cur >> (value_size - 1):
                cur |= -1 << (value_size - 1)
            
            # Update the storage
            self.data[self.position] = <cnp.int16_t> cur
            self.position += 1
            
            # Update the position in the array
            offset = offset + value_size
            pos += offset // 8
            offset %= 8    


def pack_image(img):
    """Pack an image into a binary compressed block
    
    :param img: input image as numpy.int16
    :return: 1D array of numpy.int8  
    
    JPA wrote:
    ..........
    Pack image 'img', containing 'x * y' WORD-sized pixels into byte-stream
    """
    cdef:
        int nrow, ncol, size
        cnp.int16_t[:] raw 
    assert len(img.shape) == 2
    nrow = img.shape[0]
    ncol = img.shape[1]
    
    #pre compression: subtract the average of the 4 neighbours
    raw = precomp(numpy.ascontiguous(img.ravel(), dtype=numpy.int16), ncol)
    #...
    return 


def unpack_pck(cnp.uint8_t[:] stream, int ncol, int nrow):
    """Unpack the raw stream and return the image
    V1 only for now, V2 may be added later
    
    :param stream: raw input stream
    :param ncol: number of columns in the image (i.e width)
    :param nrow: number if rows in the image (i.e. height)
    :return: decompressed image
    """
    cdef: 
        int offset, new_offset #Number of bit to offset in the current byte
        int pos, end_pos #current position and last position of block  in byte stream
        int size #size of the input stream
        int value, next # integer values 
        UnpackContainer cont 

    cont = UnpackContainer(ncol, nrow)
    size = stream.size
    # Luckily we start at byte boundary
    offset = 0
    pos = 0
    
    while pos < (size - 1) and cont.position<(cont.size -1):
        value = stream[pos]
        if offset > (8 - CCP4_PCK_BLOCK_HEADER_LENGTH):
            # wrap around
            pos += 1
            next = stream[pos]
            value |= next << 8
            offset += CCP4_PCK_BLOCK_HEADER_LENGTH - 8
        elif offset == (8 - CCP4_PCK_BLOCK_HEADER_LENGTH):
            # Exactly on the boundary
            pos += 1
            offset = 0
        else:
            # stay in same byte
            offset += CCP4_PCK_BLOCK_HEADER_LENGTH
        
        # we use 7 as mask: decimal value of 111 
        nb_val_packed = 1 << ((value >> offset) & 7)   # move from offset, read 3 lsb, take the power of 2
        nb_bit_per_val = CCP4_PCK_BIT_COUNT[(value >> (3 + offset)) & 7] # read 3 next bits, search in LUT for the size of each element in block

    if nb_bit_per_val == 0:
        cont.set_zero(nb_val_packed)

    else:
        nb_bit_in_block = nb_bit_per_val * nb_val_packed
        end_pos = pos + (new_offset + nb_bit_in_block + 7) // 8
        cont.unpack(stream[pos: end_pos + 1], offset, nb_val_packed, nb_bit_per_val)
        pos = (offset + nb_bit_in_block) // 8
        offset = (offset + nb_bit_in_block) % 8


# def parse(stream):
#     offset =0 
#     pos = 0
#     while True:
#         value = ord(stream[pos])
#         if offset>2:
#             pos += 1
#             next = ord(stream[pos])
#             value |= next << 8
#         nb_val_packed = 1 << ((value >> offset) & 7)
#         nb_bit_per_val = CCP4_PCK_BIT_COUNT[(value >> (3+offset)) & 7]
#         new_offset = (6 + offset)%8
#         if new_offset ==0: 
#             pos += 1
#         if nb_bit_per_val == 0:
#             offset = new_offset
#             print("pos: %i offset:%s 0*%s"%(pos, offset,nb_val_packed))
#         else:
#             nb_bit_in_block = nb_bit_per_val * nb_val_packed
#             end_pos = pos + (new_offset + nb_bit_in_block) // 8
#             new_offset = (new_offset + nb_bit_in_block) % 8
#             #pos=end_pos
#             print("pos: %i offset:%s %s bits x %s "%(pos, offset,nb_bit_per_val, nb_val_packed) + " ".join(format(ord(i),"08b") for i in stream[pos-1:end_pos+1]))
#             pos=end_pos
#             offset=new_offset

# def unpack_block(stream, offset, nb_value, value_size):
#     value = 0
#     pos = 0
#     res = []
#     print(" value size: %s x %s, offset: %s"%(value_size, nb_value, offset))
#     for i in range(nb_value):
#         tmp = 0
#         to_read = (value_size - offset + 7) // 8
#         print(" to_read: %s offset=%s" % (to_read,offset))
#         for j in range(to_read + 1):
#             tmp |= (ord(stream[pos + j])) << ( 8 * j)
#         cur = (tmp >> offset) & ((1<<value_size) -1)
# 
#         #change sign if most significant bit is 1
#         if cur>>(value_size-1):
#             cur |= -1<<(value_size-1)
# 
#         res.append(check_sign(cur, value_size))
#         offset = offset + value_size
#         pos += offset//8
#         offset %= 8
#     return res
