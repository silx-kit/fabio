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


cimport numpy
import numpy
import cython

@cython.boundscheck(False)
def analyseCython(bytes stream not None, size=None):
    """
    Analyze a stream of char with any length of exception (2,4, or 8 bytes integers)
    @param stream: string representing the compressed data
    @param size: the size of the output array (of longInts)
    @return : int64 ndArrays 
    """

    cdef int                i = 0
    cdef int                j = 0
    cdef long long          last = 0
    cdef long long          current = 0
    cdef char               tmp8 = 0

    cdef unsigned char      utmp8a = 0
    cdef unsigned char      utmp8b = 0
    cdef unsigned char      utmp8c = 0
    cdef unsigned char      utmp8d = 0
    cdef unsigned char      utmp8e = 0
    cdef unsigned char      utmp8f = 0
    cdef unsigned char      utmp8g = 0

    cdef long long          tmp64 = 0
    cdef long long          tmp64a = 0
    cdef long long          tmp64b = 0
    cdef long long          tmp64c = 0
    cdef long long          tmp64d = 0
    cdef long long          tmp64e = 0
    cdef long long          tmp64f = 0
    cdef long long          tmp64g = 0

    cdef char               key8 = 0x80
    cdef char               key0 = 0x00

    cdef int csize
    cdef int lenStream = < int > len(stream)
    cdef char * cstream = stream
    if size is None:
        csize = lenStream
    else:
        csize = < int > size
    cdef numpy.ndarray[ long long  , ndim = 1] dataOut = numpy.zeros(csize, dtype=numpy.int64)
    with nogil:
        while (i < lenStream) and (j < csize):
            if (cstream[i] == key8):
                if ((cstream[i + 1] == key0) and (cstream[i + 2] == key8)):
                    if (cstream[i + 3] == key0) and (cstream[i + 4] == key0) and (cstream[i + 5] == key0) and (cstream[i + 6] == key8):
                        #Retrieve the interesting Bytes of data
                        tmp8 = cstream[i + 14]
                        utmp8a = cstream[i + 13]
                        utmp8b = cstream[i + 12]
                        utmp8c = cstream[i + 11]
                        utmp8d = cstream[i + 10]
                        utmp8e = cstream[i + 9]
                        utmp8f = cstream[i + 8]
                        utmp8g = cstream[i + 7]
                        # cast them  in 64 bit
                        tmp64 = tmp8
                        tmp64a = utmp8a
                        tmp64b = utmp8b
                        tmp64c = utmp8c
                        tmp64d = utmp8d
                        tmp64e = utmp8e
                        tmp64f = utmp8f
                        tmp64g = utmp8g
                        current = (tmp64 << 56) | (tmp64a << 48) | (tmp64b << 40) | (tmp64c << 32) | (tmp64d << 24) | (tmp64e << 16) | (tmp64f << 8) | (tmp64g)
                        i += 15
                    else:
                        #Retrieve the interesting Bytes of data
                        tmp8 = cstream[i + 6]
                        utmp8a = cstream[i + 5]
                        utmp8b = cstream[i + 4]
                        utmp8c = cstream[i + 3]
                        # cast them  in 64 bit
                        tmp64 = tmp8
                        tmp64a = utmp8a
                        tmp64b = utmp8b
                        tmp64c = utmp8c
                        #Assemble data into a long long
                        current = (tmp64 << 24) | (tmp64a << 16) | (tmp64b << 8) | (tmp64c);
                        i += 7
                else:
                    tmp8 = cstream[i + 2];
                    utmp8a = cstream[i + 1]
                    # cast them  in 64 bit
                    tmp64 = tmp8
                    tmp64a = utmp8a
                    current = (tmp64 << 8) | (tmp64a);
                    i += 3
            else:
                tmp8 = cstream[i]
                current = tmp8
                i += 1
            last += current
            dataOut[j] = last
            j += 1
    return dataOut[:j]
