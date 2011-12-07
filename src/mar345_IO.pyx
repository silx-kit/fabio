import cython
cimport numpy
import numpy
import os
from libc.stdio cimport FILE
cdef extern from "numpy/arrayobject.h":
    ctypedef int intp
    ctypedef extern class numpy.ndarray [object PyArrayObject]:
        cdef char * data
        cdef int nd
        cdef intp * dimensions
        cdef intp * strides
        cdef int flags

ctypedef int LONG
ctypedef short int WORD
ctypedef char BYTE
ctypedef numpy.uint16_t NP_WORD


cdef extern from "marpck.h":
# Function: Putmar345Data (ex put_pck)
# Arguments:
# 1.)	16-bit image array
# 2.)	No. of pixels in horizontal direction (x)
# 3.)	No. of pixels in vertical   direction (y)
# 4.)	File descriptor for unbuffered I/O (-1 for unused)
# 5.)	File pointer    for buffered   I/O (NULL for unused)
    int Putmar345Data   (WORD * , int, int, int, FILE *)nogil


#@cython.cdivision(True)
#@cython.boundscheck(False)
#@cython.wraparound(False)
def compress_pck(numpy.ndarray inputArray not None, filename not None):
    """
    docstring to write

    """
    cdef long  size = inputArray.size
    cdef int dim0, dim1, i, j, fd
    assert inputArray.ndim == 2
    dim0 = inputArray.shape[0]
    dim1 = inputArray.shape[1]
    print '0x%x' % inputArray.ctypes.data
    cdef numpy.ndarray[NP_WORD, ndim = 1] data = numpy.ascontiguousarray(inputArray.astype(numpy.uint16).ravel(), dtype=numpy.uint16)
    print '0x%x' % data.ctypes.data
    cdef WORD * cdata
    cdata = < WORD *> data.data
    if os.path.exists(filename):
        fd = os.open(filename, os.O_APPEND | os.O_WRONLY)
    else:
        fd = os.open(filename, os.O_CREAT | os.O_WRONLY)
    print fd, dim1, dim0
    ret = Putmar345Data(cdata, dim1, dim0, fd, NULL)
    print "ret code", ret
    os.close(fd)




