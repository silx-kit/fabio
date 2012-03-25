"""
New Cython version of mar345_io for preparing the migration to Python3

Compressor & decompressor for "pack" algorithm by JPA, binding to CCP4 libraries 

Warning: decompressor is just a cython porting of mar345_io, but in cython so python3 compliant.

Future: make those algorithm actually generate strings not go via files;
        it will allow a broader use of the algorith 

"""

__authors__ = ["Jerome Kieffer", "gael.goret@esrf.fr"]
__contact__ = "jerome.kieffer@esrf.eu"
__license__ = "LGPLv3+"
__copyright__ = "2012, European Synchrotron Radiation Facility, Grenoble, France"

import cython
cimport numpy
import numpy
import os,tempfile
from libc.stdio cimport FILE
ctypedef int LONG
ctypedef short int WORD
ctypedef char BYTE
cdef extern from "Python.h":
    FILE * PyFile_AsFile(object)

cdef extern from "pack_c.h":
     void pack_wordimage_c(WORD*, int , int , char*) nogil
     void unpack_word(FILE *packfile, int x, int y, WORD *img) nogil

cdef extern from "ccp4_pack.h":
    void* mar345_read_data(FILE *file, int ocount, int dim1, int dim2) nogil
    
@cython.boundscheck(False)
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
    cdef numpy.ndarray[numpy.uint16_t, ndim = 1] data = numpy.ascontiguousarray(inputArray.astype(numpy.uint16).ravel(), dtype=numpy.uint16)
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

@cython.boundscheck(False)
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
    cdef numpy.ndarray[numpy.uint32_t, ndim = 2] data = numpy.zeros((cdim2, cdim1), dtype=numpy.uint32)
    cdef FILE * cFile = < FILE *> PyFile_AsFile(inFile)
    with nogil:
        data.data = <char *> mar345_read_data(cFile, chigh, cdim1, cdim2) 
    return data

