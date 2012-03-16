import cython
cimport numpy
import numpy
import os,tempfile
from libc.stdio cimport FILE
#cdef extern from "stdio.h": 
#    FILE* fdopen(int fildes, const char *type) 
ctypedef int LONG
ctypedef short int WORD
ctypedef char BYTE
ctypedef numpy.uint16_t NP_WORD
ctypedef numpy.uint32_t NP_U32
cdef extern from "Python.h":
    ctypedef struct FILE
    FILE * PyFile_AsFile(object)
    void  fprintf(FILE * f, char * s, char * s)
cdef extern from "fileobject.h":
    ctypedef class __builtin__.file [object PyFileObject]:
        pass

#cdef extern from "ccp4_pack.h":
#     void * mar345_read_data(FILE * file, int ocount, int dim1, int dim2) nogil
cdef extern from "pack_c.h":
     void pack_wordimage_c(WORD*, int , int , char*) nogil
#     void readpack_word_c(WORD *img, char *filename) nogil
#     void pack_wordimage_copen(WORD*, int , int , FILE *)nogil
     void unpack_word(FILE *packfile, int x, int y, WORD *img)nogil

@cython.cdivision(True)
@cython.boundscheck(False)
@cython.wraparound(False)
def compress_pck(numpy.ndarray inputArray not None):
    """
    @param inputArray: numpy array as input
    @param filename: file to write data to 
    """
    cdef long  size = inputArray.size
    cdef int dim0, dim1, i, j, fd, ret
    cdef char* name
    assert inputArray.ndim == 2, "shape is 2D"
    dim0 = inputArray.shape[0]
    dim1 = inputArray.shape[1]
    cdef numpy.ndarray[NP_WORD, ndim = 1] data = numpy.ascontiguousarray(inputArray.astype(numpy.uint16).ravel(), dtype=numpy.uint16)
    cdef WORD * cdata
    cdata = < WORD *> data.data
    (fd,fname) = tempfile.mkstemp()
    name = <char*>  fname
    with nogil:
        pack_wordimage_c(cdata, dim1, dim0, name)
    with open(name,"rb") as f:
        f.seek(0)
        output = f.read()
    os.close(fd)
    os.remove(name)
    return output

@cython.cdivision(True)
@cython.boundscheck(False)
@cython.wraparound(False)
def uncompress_pck(inFile not None, dim1=None, dim2=None, overflowPix=None):
    """
    Unpack a mar345 compressed image
    
    @param inFile: opened python file
    @param dim1,dim2: optional parameters size
    @param overflowPix: optional parameters: number of overflowed pixels 
    
    @return : ndarray of 2D with the right size
    """
    cdef int cdim1, cdim2, chigh
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
        hiLine = hiLine.split("\n")[0]
        word = hiLine.split()
        if len(word) > 1:
            chigh = int(word[1])
        else:
            print("Error while looking for overflowed pixels in line %s" % hiLine.strip())
            chigh = 0
    else:
        chigh = < int > overflowPix
#    inFile.close()
    cdef numpy.ndarray[NP_WORD, ndim = 2] data = numpy.zeros((cdim2, cdim1), dtype=numpy.uint16)
    cdata = < WORD * > data.data
#    inFile.seek(0)
    cdef FILE * cFile = < FILE *> PyFile_AsFile(inFile)

    with nogil:
#        cdata = mar345_read_data(cFile, chigh, cdim1, cdim2) 
        unpack_word(cFile, cdim1, cdim2,cdata)
    print("Warning ... this is under development code; I would not trust it")
    return data




