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
ctypedef numpy.uint32_t NP_U32
# Idiom for accessing Python files.
# First, declare the Python macro to access files:
cdef extern from "Python.h":
    ctypedef struct FILE
    FILE * PyFile_AsFile(object)
    void  fprintf(FILE * f, char * s, char * s)
# Next, enter the builtin file class into the namespace:
cdef extern from "fileobject.h":
    ctypedef class __builtin__.file [object PyFileObject]:
        pass
        #FILE * f_fp

cdef extern from "marpck.h":
# Function: Putmar345Data (ex put_pck)
# Arguments:
# 1.)	16-bit image array
# 2.)	No. of pixels in horizontal direction (x)
# 3.)	No. of pixels in vertical   direction (y)
# 4.)	File descriptor for unbuffered I/O (-1 for unused)
# 5.)	File pointer    for buffered   I/O (NULL for unused)
    int Putmar345Data   (WORD * , int, int, int, FILE *)nogil
    int Getmar345Data   (FILE * , WORD *)nogil

cdef extern from "ccp4_pack.h":
     void * mar345_read_data(FILE * file, int ocount, int dim1, int dim2)nogil


#@cython.cdivision(True)
#@cython.boundscheck(False)
#@cython.wraparound(False)
def compress_pck(numpy.ndarray inputArray not None, filename not None):
    """
    @param inputArray:
    @param filename: 
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


def uncompress_pck(filename not None, dim1=None, dim2=None, overflowPix=None):
    """
    Unpack a mar345 compressed image
    
    @param filename: name of the file
    @param dim1,dim2: optional parameters size
    @param overflowPix: optional parameters: number of overflowed pixels 
    
    @return : ndarray of 2D with the right size
    """
    cdef int cdim1, cdim2, chigh
    inFile = open(filename, "r")
    if dim1 is None or dim2 is None:
        raw = inFile.read()
        key1 = "CCP4 packed image, X: "
        key2 = "CCP4 packed image V2, X: "
        start = raw.find(key2)
        key = key2
        if start == -1:
            start = raw.find(key1)
            key = key1
        start = raw.index(key) + len(key)
        sizes = raw[start:start + 13]
        cdim1 = < int > int(sizes[:4])
        cdim2 = < int > int(sizes[-4:])
    else:
        raw = None
        cdim1 = < int > dim1
        cdim2 = < int > dim2
    if overflowPix is None:
        if raw is None:
            raw = inFile.read()
        end = raw.find("END OF HEADER")
        start = raw[:end].find("HIGH")
        hiLine = raw[start:end]
        print hiLine
        hiLine = hiLine[:hiLine.find("\n")]
        word = hiLine.split()
        if len(word) > 1:
            chigh = int(word[1])
        else:
            print("Error while looking for overflowed pixels in line %s" % hiLine.strip())
            chigh = 0
    else:
        chigh = < int > overflowPix

    cdef numpy.ndarray[NP_WORD, ndim = 2] data = numpy.zeros((cdim2, cdim1), dtype=numpy.uint16)
    cdata = < WORD * > data.data
    cdef FILE * cFile = < FILE *> PyFile_AsFile(inFile)
    with nogil:
        ret = Getmar345Data(cFile, cdata)
    print "ret code", ret

#    cdef numpy.ndarray[NP_U32, ndim = 2] data = numpy.zeros((cdim2, cdim1), dtype=numpy.uint32)
#    data.data = < char *> mar345_read_data(< FILE *> PyFile_AsFile(inFile), chigh, cdim1, cdim2)

    inFile.close()
    return data




