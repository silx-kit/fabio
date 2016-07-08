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


"""
Eiger data file reader for FabIO

Eiger data files are HDF5 files with one group called "entry" and a dataset 
called "data" in it. The dataset is usually compressed using LZ4 compression.

H5py (>2.5) and libhdf5 (>1.8.10) with the compression plugin are needed  

"""
# Get ready for python3:
from __future__ import with_statement, print_function, division

__authors__ = ["Jérôme Kieffer"]
__contact__ = "jerome.kieffer@esrf.fr"
__license__ = "MIT"
__copyright__ = "ESRF"
__date__ = "08/07/2016"

import logging
logger = logging.getLogger("numpyimage")

try:
    import h5py
except ImportError:
    h5py = None

from .fabioimage import FabioImage
from .fabioutils import NotGoodReader


class EigerImage(FabioImage):
    """
    FabIO image class for Images from Eiger data files (HDF5)
    
    """
    def __init__(self, data=None, header=None):
        """
        Set up initial values
        """
        if not h5py:
            raise RuntimeError("fabio.EigerImage cannot be used without h5py. Please install h5py and restart")

        FabioImage.__init__(self, data, header)
        self.dataset = data

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
        h5file = h5py.File(fname, mode="r")
        try:
            self.dataset = h5file["entry/data"]
        except KeyError:
            raise NotGoodReader("Eiger data file contain 'entry/data' structure in the HDF5 file.")
        if isinstance(self.dataset, h5py.Group) and "data" in self.dataset.keys():
            self.dataset = self.dataset["data"]
        self.nframes = self.dataset.shape[0]
        self._dim1 = self.dataset.shape[-1]
        self._dim2 = self.dataset.shape[-2]
        if frame is not None:
            self.currentframe = int(frame)
        else:
            self.currentframe = 0
        self.data = self.dataset[self.currentframe, :, :]
        return self

    def write(self, fname):
        """
        try to write image 
        @param fname: name of the file 
        """
        if len(self.dataset.shape) == 2:
            self.dataset.shape = (1,) + self.dataset.shape
        with h5py.File(fname) as h5file:
            grp = h5file.require_group("entry")
            grp["data"] = self.dataset

    def getframe(self, num):
        """ returns the frame numbered 'num' in the stack if applicable"""
        if self.nframes > 1:
            new_img = None
            if (num >= 0) and num < self.nframes:
                data = self.dataset[num]
                new_img = self.__class__(data=data, header=self.header)
                new_img.dataset = self.dataset
                new_img.nframes = self.nframes
                new_img.currentframe = num
            else:
                raise RuntimeError("getframe %s out of range [%s %s[" % (num, 0, self.nframes))
        else:
            new_img = FabioImage.getframe(self, num)
        return new_img

    def previous(self):
        """ returns the previous frame in the series as a fabioimage """
        return self.getframe(self.currentframe - 1)

    def next(self):
        """ returns the next frame in the series as a fabioimage """
        return self.getframe(self.currentframe + 1)

eigerimage = EigerImage
