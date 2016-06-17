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
Eiger data file reader for FabIO

Eiger data files are HDF5 files with one group called "entry" and a dataset 
called "data" in it. The dataset is usually compressed using LZ4 compression.

H5py (>2.5) and libhdf5 (>1.8.10) with the compression plugin are needed  

"""
# Get ready for python3:
from __future__ import with_statement, print_function, division

__authors__ = ["Jérôme Kieffer"]
__contact__ = "jerome.kieffer@esrf.fr"
__license__ = "GPLv3+"
__copyright__ = "ESRF"
__date__ = "17/06/2016"

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
        self.nframes = self.dataset.shape[0]
        self._dim1 = self.dataset[-1]
        self._dim2 = self.dataset[-2]
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
