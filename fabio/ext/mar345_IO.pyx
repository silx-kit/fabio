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
__date__ = "12/09/2016" 

import cython
cimport numpy as cnp

import numpy
import os
import tempfile


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
def uncompress_pck(bytes raw not None, dim1=None, dim2=None, overflowPix=None, version=None, normal_start=None, swap_needed=None, bint use_cython=False):
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
        cnp.uint32_t[:, ::1] data
        cnp.uint8_t[::1] instream
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

    instream = numpy.fromstring(raw[normal_offset:].lstrip(), dtype=numpy.uint8)

    if use_cython:
        unpacked = postdec(unpack_pck(instream, cdimx, cdimy).get1d(), cdimx)
        data = numpy.ascontiguousarray(unpacked, numpy.uint32).reshape((cdimy, cdimx))
    else:
        data = numpy.empty((cdimy, cdimx), dtype=numpy.uint32)   
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
# Re-Implementation of the pck compression/decompression 
################################################################################
@cython.boundscheck(False)
@cython.cdivision(True)
cpdef any_int_t[::1] precomp(any_int_t[::1] img, int width):
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
        size_t size, i
        any_int_t[::1] comp
        any_int_t last, cur, im0, im1, im2
    size = img.size
    comp = numpy.zeros_like(img)
    
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
        comp[i] = cur - (last + im0 + im1 + im2 + 2) // 4
        last = cur
        im0 = im1
        im1 = im2
        im2 = img[i - width + 2]

    return comp


@cython.boundscheck(False)
@cython.cdivision(True)
cpdef any_int_t[::1] postdec(any_int_t[::1] comp, int width):
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
        size_t size, i
        any_int_t[::1] img
        any_int_t last, cur, fl0, fl1, fl2
    size = comp.size
    img = numpy.zeros_like(comp)
    
    # First pixel
    img[0] = last = comp[0] 
    
    # First line (+ 1 pixel)
    for i in range(1, width + 1):
        img[i] = cur = comp[i] + last  
        last = cur
    
    # Rest of the image: not parallel in this case
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
 
    
cpdef int calc_nb_bits(any_int_t[::1] data):
    """Calculate the number of bits needed to encode the data
    
    :param data: input data, probably slices of a larger array
    :return: the needed number of bits to store the values
    
    Comment from JPA:
    .................
    
    Returns the number of bits necessary to encode the longword-array 'chunk'
    of size 'n' The size in bits of one encoded element can be 0, 4, 5, 6, 7,
    8, 16 or 32.
     """ 
    cdef size_t size, maxsize, i
    
    size = data.size
    maxsize = 0
    
    for i in range(size):
        maxsize = max(maxsize, abs(data[i]))
    if maxsize == 0:
        return = 0
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
        return size *= 32


cdef class UnpackContainer:
    cdef:
        readonly size_t nrow, ncol, position, size
        cnp.int32_t[::1] data 
    
    def __cinit__(self, int ncol, int nrow):
        self.nrow = nrow
        self.ncol = ncol
        self.size = nrow * ncol
        self.data = numpy.zeros(self.size, dtype=numpy.int32)
        self.position = 0
    
    def __dealloc__(self):
        self.data = None
        
    def [:, ::1] get(self):
        """retrieve the populated array"""
        return numpy.asarray(self.data).reshape((self.ncol, self.nrow))

    cpdef cnp.int32_t[::1] get1d(self):
        """retrieve the populated array"""
        return numpy.asarray(self.data)

    cpdef set_zero(self, int number):
        "set so many zeros"
        self.position += number
        
    @cython.boundscheck(False)
    @cython.cdivision(True)
    cpdef unpack(self, cnp.uint8_t[::1] stream, int pos, int offset, int nb_value, int value_size):
        """unpack a block on data, all the same size
        
        :param stream: input stream, already sliced
        :param offset: number of bits of offset, at the begining of the stream 
        :param nb_value: number of values to unpack
        :param value_size: number of bits of each value
        """
        cdef:
            int i, j        # simple counters
            int value       # value to be stored
            cnp.uint64_t tmp# under contruction: needs to be unsigned
            int to_read     # number of bytes to read
            int new_offset  # position after read 
        value = 0

        for i in range(nb_value):
            tmp = 0
            # read as many bytes as needed and unpack them to tmp variable
            new_offset = value_size + offset 
            to_read = (new_offset + 7) // 8
            
            for j in range(to_read + 1):
                tmp |= (stream[pos + j]) << (8 * j)
            # Remove the lsb of tmp up to offset and apply the mask
             
            cur = (tmp >> offset) & ((1 << value_size) - 1)
            
            # change sign if most significant bit is 1
            if cur >> (value_size - 1):
                cur |= -1 << (value_size - 1)

            # Update the storage
            self.data[self.position] = cur
            self.position += 1
            
            # Update the position in the array
            pos += new_offset // 8
            offset = new_offset % 8    


def pack_image(img, do_precomp=True):
    """Pack an image into a binary compressed block
    
    :param img: input image as numpy.int16
    :param do_precomp: perform the subtraction to the 4 neighbours's average. False is for testing the packing only 
    :return: 1D array of numpy.int8  
    
    JPA wrote:
    ..........
    Pack image 'img', containing 'x * y' WORD-sized pixels into byte-stream
    """
    cdef:
        int nrow, ncol, size, stream_size
        cnp.int16_t[::1] input_image, raw 
        PackContainer container
        size_t i, position
        size_t nb_val_packed
    assert len(img.shape) == 2
    nrow = img.shape[0]
    ncol = img.shape[1]
    
    if do_precomp:
        input_image = (numpy.ascontiguousarray(img.ravel(), dtype=numpy.int16))
        # pre compression: subtract the average of the 4 neighbours
        raw = precomp(input_image, ncol)
    else:
        raw = numpy.ascontiguousarray(img.ravel(), dtype=numpy.int16)
    
    # allocation of the output buffer
    size = nrow * ncol
    container = PackContainer(size)
    position = 0
    while position < size:
        nb_val_packed = 1
        while (position + nb_val_packed) < size and nb_val_packed < 128:
            current_block_size = calc_nb_bits(raw[position: position + nb_val_packed])
            if (position + 2 * nb_val_packed) < size:
                next_bock_size = calc_nb_bits(raw[position + nb_val_packed: position + 2 * nb_val_packed])
            else:
                break
            if 2 * max(current_block_size, next_bock_size) < (current_block_size + next_bock_size + CCP4_PCK_BLOCK_HEADER_LENGTH):
                nb_val_packed *= 2
                current_block_size *= 2
            else:
                break
#         print(position, nb_val_packed, current_block_size // nb_val_packed)
        container.append(raw, position, nb_val_packed, current_block_size)
        position += nb_val_packed
                         
    return numpy.asarray(container.get())


cdef class PackContainer:
    cdef: 
        readonly size_t position, offset, allocated
        cnp.uint8_t[::1] data 
    
    def __cinit__(self, size_t size=4096):
        """Constructor of the class
        
        :param size: start size of the array
        """
        self.position = 0
        self.offset = 0
        self.allocated = size
        self.data = numpy.zeros(self.allocated, dtype=numpy.uint8)
    
    def __dealloc__(self):
        self.data = None
        
    cpdef cnp.uint8_t[::1] get(self):
        """retrieve the populated array"""
        if self.offset:
            end = self.position + 1
        else:
            end = self.position
        return numpy.asarray(self.data[:end])
    
    cpdef append(self, cnp.int16_t[::1] data, size_t position, size_t nb_val, size_t block_size): 
        """Append a block of data[position: position+nb_val] to the compressed
        stream. Only the most significant bits are takes.
        
        :param data: input uncompressed image as 1D array
        :param position: start position of reading of the image
        :param nb_val: number of value from data to pack in the block
        :param block_size: number of bits for the whole block
        
        The 6 bits header is managed here as well as the stream resizing.
        """
        cdef:
            size_t offset, index, i, bit_per_val, nb_bytes
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
        
        if bit_per_val == 0:
            return
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
            

cpdef cnp.uint8_t pack_nb_val(cnp.uint8_t nb_val, cnp.uint8_t value_size):
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


@cython.boundscheck(False)
@cython.cdivision(True)
cpdef UnpackContainer unpack_pck(cnp.uint8_t[::1] stream, int ncol, int nrow):
    """Unpack the raw stream and return the image
    V1 only for now, V2 may be added later
    
    :param stream: raw input stream
    :param ncol: number of columns in the image (i.e width)
    :param nrow: number if rows in the image (i.e. height)
    :return: Container with decompressed image
    """
    cdef: 
        size_t offset       #Number of bit to offset in the current byte
        size_t pos, end_pos #current position and last position of block  in byte stream
        size_t size         #size of the input stream
        int value, next  # integer values 
        size_t nb_val_packed, nb_bit_per_val, nb_bit_in_block
        UnpackContainer cont #Container with unpacked data 

    cont = UnpackContainer(ncol, nrow)
    size = stream.size
    
    # Luckily we start at byte boundary
    offset = 0
    pos = 0
    
    while pos < (size - 1) and cont.position < (cont.size - 1):
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
        nb_val_packed = 1 << (value & 7)   # move from offset, read 3 lsb, take the power of 2
        nb_bit_per_val = CCP4_PCK_BIT_COUNT[(value >> 3) & 7] # read 3 next bits, search in LUT for the size of each element in block

        if nb_bit_per_val == 0:
            cont.set_zero(nb_val_packed)
        else:
            nb_bit_in_block = nb_bit_per_val * nb_val_packed
            #
            #try:
            cont.unpack(stream, pos, offset, nb_val_packed, nb_bit_per_val)
#             except IndexError as err:
#                 print("**IndexError**: %s" % err)
#                 end_pos = pos + (offset + nb_bit_in_block + 7) // 8
#                 print(pos, end_pos, stream.size)
#                 print(offset, nb_val_packed, nb_bit_per_val)
#                 print(cont.size, cont.position)
#                 break
            offset += nb_bit_in_block
            pos += offset // 8
            offset %= 8
#             break
    return cont

    
