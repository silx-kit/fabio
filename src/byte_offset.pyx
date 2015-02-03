"""
Authors:      Jerome Kieffer, ESRF
Email:        jerome.kieffer@esrf.eu

Cif Binary Files images are 2D images written by the Pilatus detector and others.
They use a modified (simplified) byte-offset algorithm.  This file contains the
decompression function from a string to an int64 numpy array.

This is Cython: convert it to pure C then compile it with gcc
$ cython byte_offset.pyx

"""

__author__ = "Jerome Kieffer"
__contact__ = "jerome.kieffer@esrf.eu"
__license__ = "LGPLv3+"
__copyright__ = "2010-2012, European Synchrotron Radiation Facility, Grenoble, France"
__date__ = "03/02/2015"


cimport numpy
import numpy
import cython

@cython.boundscheck(False)
def analyseCython(bytes stream not None, size=None):
    """
    Analyze a stream of char with any length of exception (2,4, or 8 bytes integers)
    @param stream: bytes (string) representing the compressed data
    @param size: the size of the output array (of longInts)
    @return : int64 ndArrays
    """
    cdef:
        int               i = 0
        int               j = 0
        numpy.uint8_t     tmp8 = 0

        numpy.int64_t    last = 0
        numpy.int64_t    current = 0
        numpy.int64_t    tmp64 = 0
        numpy.int64_t    tmp64a = 0
        numpy.int64_t    tmp64b = 0
        numpy.int64_t    tmp64c = 0
        numpy.int64_t    tmp64d = 0
        numpy.int64_t    tmp64e = 0
        numpy.int64_t    tmp64f = 0
        numpy.int64_t    tmp64g = 0

        numpy.uint8_t    key8 = 0x80
        numpy.uint8_t    key0 = 0x00

        int csize
        int lenStream = < int > len(stream)
        numpy.uint8_t[:] cstream = bytearray(stream)
    if size is None:
        csize = lenStream
    else:
        csize = < int > size
    cdef numpy.ndarray[numpy.int64_t, ndim = 1] dataOut = numpy.zeros(csize, dtype=numpy.int64)
    with nogil:
        while (i < lenStream) and (j < csize):
            if (cstream[i] == key8):
                if ((cstream[i + 1] == key0) and (cstream[i + 2] == key8)):
                    if (cstream[i + 3] == key0) and (cstream[i + 4] == key0) and (cstream[i + 5] == key0) and (cstream[i + 6] == key8):
                        # Retrieve the interesting Bytes of data
                        tmp64g = cstream[i + 7]
                        tmp64f = cstream[i + 8]
                        tmp64e = cstream[i + 9]
                        tmp64d = cstream[i + 10]
                        tmp64c = cstream[i + 11]
                        tmp64b = cstream[i + 12]
                        tmp64a = cstream[i + 13]
                        tmp64  = <numpy.int8_t> cstream[i + 14]
                        # Assemble data into a 64 bits integer
                        current = (tmp64 << 56) | (tmp64a << 48) | (tmp64b << 40) | (tmp64c << 32) | (tmp64d << 24) | (tmp64e << 16) | (tmp64f << 8) | (tmp64g)
                        i += 15
                    else:
                        # Retrieve the interesting Bytes of data
                        tmp64c = cstream[i + 3]
                        tmp64b = cstream[i + 4]
                        tmp64a = cstream[i + 5]
                        tmp64  = <numpy.int8_t> cstream[i + 6]
                        # Assemble data into a 64 bits integer
                        current = (tmp64 << 24) | (tmp64a << 16) | (tmp64b << 8) | (tmp64c);
                        i += 7
                else:
                    tmp64a = cstream[i + 1]
                    tmp64  = <numpy.int8_t> cstream[i + 2];

                    current = (tmp64 << 8) | (tmp64a);
                    i += 3
            else:
                current = (<numpy.int8_t> cstream[i])
                i += 1
            last += current
            dataOut[j] = last
            j += 1

    return dataOut[:j]
