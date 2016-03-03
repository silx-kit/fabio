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

"""New Cython version of cf_iomodule.c for preparing the migration to Python3"""

__authors__ = ["Jerome Kieffer"]
__contact__ = "jerome.kieffer@esrf.eu"
__license__ = "MIT"
__copyright__ = "2013, European Synchrotron Radiation Facility, Grenoble, France"

import cython
cimport numpy
import numpy
import os
import tempfile
import sys

from libc.string cimport memcpy
from libc.stdio cimport fopen, FILE

CF_H = 1

CF_INIT_ROWS = 8192
CF_INIT_COLS = 32
CF_HEADER_ITEM = 128


CF_GZ_COMP = 1
CF_BIN = 2


cdef extern from "columnfile.h":
    struct cf_data:
        int ncols,nrows
        unsigned int nralloc
        double **data
        char **clabels
    void * cf_read_ascii(void *fp, void *dest, unsigned int FLAGS)nogil
    void * cf_read_bin(void *fp, void *dest, unsigned int FLAGS)nogil
    int cf_write(char *fname, void *cf_handle, unsigned int FLAGS)nogil
    int cf_write_bin(void *fp, void *cf_handle)nogil
    int cf_write_ascii(void *fp, void *cf_handle,unsigned int FLAGS)nogil
    void cf_free( cf_data *cf_handle)nogil



def read(py_file, mode="a"):
    """
    Call the c-columnfile reading interface.
    The mode keyword argument is either:
    "a" for ascii (the default)
    "b" for binary
    """
    cdef cf_data *cf__
    cdef unsigned int flags=0,fd

#    /* perhaps not const */
    cdef int i
    cdef FILE *file

    #Here is a big issue !!! and I got an even worse solution !
#    file=PyFile_AsFile(py_file);
    (fd, fname) = tempfile.mkstemp()
    os.fdopen(fd, mode="wb").write(py_file.read())
    os.close(fd)
    file = fopen(fname, "r")

    if "z" in mode:
        flags |= CF_GZ_COMP
    if "b" in mode:
        cf__ = <cf_data *> cf_read_bin(file,NULL,flags)
    elif "a" in mode:
        cf__ =  <cf_data *> cf_read_ascii(file,NULL,flags)
    else:
        sys.stderr.write("unrecognized mode for columnfile %s (assuming ascii)\n",mode)
        cf__ =  <cf_data *> cf_read_ascii(file,NULL,flags);
#    check for failure to read
    if (cf__ == NULL):
        return None, None
    dims = (cf__.nrows, cf__.ncols)

    #since data may be non-contigous we can't simply create a numpy-array from cf__->data, as Numpy's memory model prohibits it
    # i.e. py_data=(PyArrayObject*)PyArray_SimpleNewFromData(2, dims, NPY_DOUBLE, (void*)(&(cf__->data[0][0])));
    # won't work
    cdef numpy.ndarray[numpy.float64_t, ndim = 2] py_data = numpy.empty(dims,dtype=numpy.float64)
    for i in range(cf__.nrows):
        memcpy(&py_data[i,0], cf__.data[i],cf__.ncols*sizeof(double))
    clabels = []
    for i in range(cf__.ncols):
        clabels.append(str(cf__.clabels[i]))
    cf_free(cf__)

    return py_data, clabels
