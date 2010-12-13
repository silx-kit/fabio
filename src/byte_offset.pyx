cimport numpy
import numpy
import cython
import struct

@cython.boundscheck(False)
def analyseCython(char* stream, int size):
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

    cdef char               key8 = 0x80
    cdef char               key0 = 0x00
    cdef numpy.ndarray[ long long  , ndim = 1] dataOut 
    dataOut = numpy.zeros(size, dtype=numpy.int64)

    with nogil:
        while (j < size):
            if (stream[i] == key8):
                if ((stream[i + 1] == key0) and (stream[i + 2] == key8)):
                    if (stream[i + 3] == key0) and (stream[i + 4] == key0) and (stream[i + 5] == key0) and (stream[i + 6] == key8):
                        tmp8 = stream[i + 14]
                        utmp8a = stream[i + 13]
                        utmp8b = stream[i + 12]
                        utmp8c = stream[i + 11] 
                        utmp8d = stream[i + 10]
                        utmp8e = stream[i + 9]
                        utmp8f = stream[i + 8] 
                        utmp8g = stream[i + 7]
                        current = (tmp8 << 56) | (utmp8a << 48) | (utmp8b << 40) | (utmp8c << 32) | (utmp8d << 24) | (utmp8e << 16) | (utmp8f << 8) | (utmp8g)
                        i += 15
                    else:
                        tmp8 = stream[i + 6]
                        utmp8a = stream[i + 5]
                        utmp8b = stream[i + 4]
                        utmp8c = stream[i + 3] 
                        current = (tmp8 << 24) | (utmp8a << 16) | (utmp8b << 8) | (utmp8c);
                        i += 7
                else:
                    tmp8 = stream[i + 2];
                    utmp8a = stream[i + 1]
                    current = (tmp8 << 8) | (utmp8a);
                    i += 3
            else:
                tmp8 = stream[i]
                current = tmp8
                i += 1
            last += current
            dataOut[j] = last
            j += 1

    return dataOut
