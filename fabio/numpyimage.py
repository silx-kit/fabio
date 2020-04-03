# coding: utf-8
#
#    Project: FabIO X-ray image reader
#
#    Copyright (C) 2010-2016 European Synchrotron Radiation Facility
#                       Grenoble, France
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
#

"""Generic numpy file reader for FabIO"""

__authors__ = ["Jérôme Kieffer"]
__contact__ = "jerome.kieffer@esrf.fr"
__license__ = "MIT"
__copyright__ = "ESRF"
__date__ = "03/04/2020"

import logging
logger = logging.getLogger(__name__)
import numpy
from . import fabioimage


class NumpyImage(fabioimage.FabioImage):
    """
    FabIO image class for Images for numpy array dumps

    Source: http://docs.scipy.org/doc/numpy/neps/npy-format.html

    Format Specification: Version 1.0::

        The first 6 bytes are a magic string: exactly “x93NUMPY”.

        The next 1 byte is an unsigned byte: the major version number of the file
        format, e.g. x01.

        The next 1 byte is an unsigned byte: the minor version number of the file
        format, e.g. x00.
        Note: the version of the file format is not tied to the version of the numpy
        package.

        The next 2 bytes form a little-endian unsigned short int: the length of the
        header data HEADER_LEN.

        The next HEADER_LEN bytes form the header data describing the array’s
        format. It is an ASCII string which contains a Python literal expression of
        a dictionary. It is terminated by a newline (‘n’) and padded with
        spaces (‘x20’) to make the total length of the magic string + 4 + HEADER_LEN
        be evenly divisible by 16 for alignment purposes.

        The dictionary contains three keys:

            “descr” : dtype.descr
                An object that can be passed as an argument to the numpy.dtype()
                constructor to create the array’s dtype.
            “fortran_order” : bool
                Whether the array data is Fortran-contiguous or not.
                Since Fortran-contiguous arrays are a common form of
                non-C-contiguity, we allow them to be written directly
                to disk for efficiency.
            “shape” : tuple of int
                The shape of the array.

        For repeatability and readability, this dictionary is formatted using
        pprint.pformat() so the keys are in alphabetic order.

        Following the header comes the array data. If the dtype contains Python
        objects (i.e. dtype.hasobject is True), then the data is a Python pickle of
        the array. Otherwise the data is the contiguous (either C- or Fortran-,
        depending on fortran_order) bytes of the array. Consumers can figure out the
        number of bytes by multiplying the number of elements given by the shape
        (noting that shape=() means there is 1 element) by dtype.itemsize.

    Format Specification: Version 2.0::

        The version 1.0 format only allowed the array header to have a total size of
        65535 bytes. This can be exceeded by structured arrays with a large number
        of columns. The version 2.0 format extends the header size to 4 GiB.
        numpy.save will automatically save in 2.0 format if the data requires it,
        else it will always use the more compatible 1.0 format.

        The description of the fourth element of the header therefore has become:

        The next 4 bytes form a little-endian unsigned int: the length of the
        header data HEADER_LEN.
    """

    DESCRIPTION = "Numpy array file format"

    DEFAULT_EXTENSIONS = ["npy"]

    def __init__(self, data=None, header=None):
        """
        Set up initial values
        """
        fabioimage.FabioImage.__init__(self, data, header)
        self.dataset = self.data
        self.slice_dataset()
        self.filename = "Numpy_array_%x" % id(self.dataset)

    def slice_dataset(self, frame=None):
        if self.dataset is None:
            return
        if self.dataset.ndim > 3:
            shape = self.dataset.shape[-2:]
            self.dataset.shape = (-1,) + shape
        elif self.dataset.ndim < 2:
            self.dataset.shape = 1, -1

        if self.dataset.ndim == 2:
            self.data = self.dataset
        elif self.dataset.ndim == 3:
            self._nframes = self.dataset.shape[0]
            if frame is None:
                frame = 0
            if frame < self.nframes:
                self.data = self.dataset[frame]
            self.currentframe = frame

    def _readheader(self, infile):
        """
        Read and decode the header of an image:

        :param infile: Opened python file (can be stringIO or bzipped file)
        """
        # list of header key to keep the order (when writing)
        self.header = self.check_header()
        infile.seek(0)

    def read(self, fname, frame=None):
        """
        Try to read image

        :param fname: name of the file
        """

        self.resetvals()
        infile = self._open(fname)
        self._readheader(infile)

        # read the image data
        self.dataset = numpy.load(infile, allow_pickle=False)
        self.slice_dataset(frame)
        return self

    def write(self, fname):
        """
        Try to write image

        :param fname: name of the file
        """
        if self.dataset is None and self.data is not None:
            self.dataset = self.data
        numpy.save(fname, self.dataset)

    def _get_frame(self, num):
        """Inherited function returning a FabioFrame"""
        if self.nframes > 1:
            if (num >= 0) and num < self.nframes:
                data = self.dataset[num]
                header = self.header.copy()
                frame = fabioimage.FabioFrame(data=data, header=header)
                frame._set_container(self, num)
                frame._set_file_container(self, num)
            else:
                raise IndexError("getframe %s out of range [%s %s[" % (num, 0, self.nframes))
        else:
            frame = fabioimage.FabioImage._get_frame(self, num)
        return frame

    def getframe(self, num):
        """ returns the frame numbered 'num' in the stack if applicable"""
        if self.nframes > 1:
            frame = None
            if (num >= 0) and num < self.nframes:
                data = self.dataset[num]
                frame = self.__class__(data=data, header=self.header)
                frame.dataset = self.dataset
                frame._nframes = self.nframes
                frame.currentframe = num
            else:
                raise IndexError("getframe %s out of range [%s %s[" % (num, 0, self.nframes))
        else:
            frame = fabioimage.FabioImage.getframe(self, num)
        return frame

    def previous(self):
        """ returns the previous frame in the series as a fabioimage """
        return self.getframe(self.currentframe - 1)

    def next(self):
        """ returns the next frame in the series as a fabioimage """
        return self.getframe(self.currentframe + 1)


numpyimage = NumpyImage
