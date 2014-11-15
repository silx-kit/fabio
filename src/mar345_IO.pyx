"""
New Cython version of mar345_io for preparing the migration to Python3

Compressor & decompressor for "pack" algorithm by JPA, binding to CCP4 libraries

Warning: decompressor is just a cython porting of mar345_io, but in cython so (soon) python3 compliant.

Future: make those algorithm actually generate strings not go via files;
        it will allow a broader use of the algorithm.

"""

__authors__ = ["Jerome Kieffer", "Gael Goret"]
__contact__ = "jerome.kieffer@esrf.eu"
__license__ = "LGPLv3+"
__copyright__ = "2012-2014, European Synchrotron Radiation Facility, Grenoble, France"

import cython
cimport numpy
import numpy
import os,tempfile

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
        numpy.uint16_t[:] data
    assert inputArray.ndim == 2, "shape is 2D"
    dim0 = inputArray.shape[0]
    dim1 = inputArray.shape[1]
    data = numpy.ascontiguousarray(inputArray.astype(numpy.uint16).ravel(), dtype=numpy.uint16)

    (fd,fname) = tempfile.mkstemp()
    name = <char*>  fname
    with nogil:
        pack_wordimage_c(< short int *> &data[0], dim1, dim0, name)
    with open(name,"rb") as f:
        f.seek(0)
        output = f.read()
    os.close(fd)
    os.remove(name)
    return output

@cython.boundscheck(False)
@cython.cdivision(True)
def uncompress_pck(raw not None, dim1=None, dim2=None, overflowPix=None, version=None, normal_start=None):
    """
    Unpack a mar345 compressed image

    @param raw: input string (bytes in python3)
    @param dim1,dim2: optional parameters size
    @param overflowPix: optional parameters: number of overflowed pixels
    @param version: PCK version 1 or 2
    @param normal_start: position of the normal value section (can be auto-guessed)
    @return : ndarray of 2D with the right size
    """
    cdef:
        int cdimx, cdimy, chigh, cversion, records, normal_offset, address, lenkey, value, i, stop
        numpy.ndarray[numpy.uint32_t, ndim = 2] data
        numpy.uint32_t[:] flat
        numpy.ndarray[numpy.uint8_t, ndim = 1] instream
        numpy.int32_t[:] odata
        void* out
    end=None
    key1 = "CCP4 packed image, X: "
    key2 = "CCP4 packed image V2, X: "

    if (dim1 is None) or (dim2 is None) or (version not in [1,2]) or (version is None) or (normal_start is None):
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
        if cversion==1:
            lenkey = len(key1)
        else:
            lenkey = len(key2)
    if cversion not in [1,2]:
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
    flat = data.ravel() #flat view on the data
    instream = numpy.fromstring(raw[normal_offset:].lstrip(),dtype=numpy.uint8)
    with nogil:
        ################################################################################
        #      relay to whichever version of ccp4_unpack is appropriate
        ################################################################################
        if cversion == 1:
            ccp4_unpack_string( &data[0,0], &instream[0], cdimx, cdimy,0);
        else:
            # cversion == 2:
            ccp4_unpack_v2_string( &data[0,0], &instream[0], cdimx, cdimy,0);
    ################################################################################
    # handle overflows: Each record is 8 overflow of 2x32bits integers
    ################################################################################
    records = (chigh + PACK_SIZE_HIGH - 1) // PACK_SIZE_HIGH
    stop = normal_offset - lenkey - 14
    odata = numpy.fromstring(raw[stop-64*records: stop], dtype=numpy.int32)
    for i in range(records*8):
        address = odata[2*i]
        value = odata[2*i+1]
        if address>0 and address<=(cdimx*cdimy):
            flat[address-1] = <numpy.uint32_t> value
    return data
