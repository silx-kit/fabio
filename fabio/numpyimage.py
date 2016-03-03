# coding: utf-8
#
#    Project: X-ray image reader
#             https://github.com/kif/fabio
#
#
#    Copyright (C) European Synchrotron Radiation Facility, Grenoble, France
#
#    Principal author:       Jérôme Kieffer (Jerome.Kieffer@ESRF.eu)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#


"""
Template for FabIO

Authors: Who are you ?
email:  Where can you be reached ?

"""
# Get ready for python3:
from __future__ import with_statement, print_function, division

__authors__ = ["Jerome Kieffer"]
__contact__ = "jerome.kieffer@esrf.fr"
__license__ = "GPLv3+"
__copyright__ = "ESRF"
__date__ = "30/10/2015"

import logging
logger = logging.getLogger("numpyimage")
import numpy
from .fabioimage import FabioImage



class NumpyImage(FabioImage):
    """
    FabIO image class for Images for numpy array dumps
    
    Source: http://docs.scipy.org/doc/numpy/neps/npy-format.html 
    
Format Specification: Version 1.0
=================================

The first 6 bytes are a magic string: exactly “x93NUMPY”.

The next 1 byte is an unsigned byte: the major version number of the file 
format, e.g. x01.

The next 1 byte is an unsigned byte: the minor version number of the file format, e.g. x00. 
Note: the version of the file format is not tied to the version of the numpy package.

The next 2 bytes form a little-endian unsigned short int: the length of the 
header data HEADER_LEN.

The next HEADER_LEN bytes form the header data describing the array’s format. 
It is an ASCII string which contains a Python literal expression of a dictionary. 
It is terminated by a newline (‘n’) and padded with spaces (‘x20’) to make the
total length of the magic string + 4 + HEADER_LEN be evenly divisible by 16 for 
alignment purposes.

The dictionary contains three keys:

    “descr” : dtype.descr
        An object that can be passed as an argument to the numpy.dtype() constructor 
        to create the array’s dtype.
    “fortran_order” : bool
        Whether the array data is Fortran-contiguous or not. 
        Since Fortran-contiguous arrays are a common form of 
        non-C-contiguity, we allow them to be written directly 
        to disk for efficiency.
    “shape” : tuple of int
        The shape of the array.

For repeatability and readability, this dictionary is formatted using 
pprint.pformat() so the keys are in alphabetic order.

Following the header comes the array data. If the dtype contains Python objects 
(i.e. dtype.hasobject is True), then the data is a Python pickle of the array. 
Otherwise the data is the contiguous (either C- or Fortran-, depending on fortran_order) 
bytes of the array. Consumers can figure out the number of bytes by multiplying the 
number of elements given by the shape (noting that shape=() means there is 1 element) 
by dtype.itemsize.

Format Specification: Version 2.0
=================================

The version 1.0 format only allowed the array header to have a total size of 65535 bytes. 
This can be exceeded by structured arrays with a large number of columns. 
The version 2.0 format extends the header size to 4 GiB. 
numpy.save will automatically save in 2.0 format if the data requires it, 
else it will always use the more compatible 1.0 format.

The description of the fourth element of the header therefore has become:

    The next 4 bytes form a little-endian unsigned int: the length of the header data HEADER_LEN.


    
    """

    def _readheader(self, infile):
        """
        Read and decode the header of an image:
        
        @param infile: Opened python file (can be stringIO or bzipped file)  
        """
        # list of header key to keep the order (when writing)
        self.header = self.check_header()
        infile.seek(0)

    def read(self, fname, frame=None):
        """
        try to read image 
        @param fname: name of the file
        """

        self.resetvals()
        infile = self._open(fname)
        self._readheader(infile)

        # read the image data
        self.data = numpy.load(infile)
        self.bytecode = self.data.dtype
        self.dim2, self.dim1 = self.data.shape
        return self

    def write(self, fname):
        """
        try to write image 
        @param fname: name of the file 
        """
        numpy.save(fname, self.data)


numpyimage = NumpyImage
