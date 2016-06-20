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
HDF5 image for FabIO

Authors: Jerome Kieffer
email:  Jerome.Kieffer@terre-adelie.org

Specifications:
input should being the form:

filename::path

if the shape>2, it will be re-shaped as 

"""
# Get ready for python3:
from __future__ import with_statement, print_function, division

__authors__ = ["Jérôme Kieffer"]
__contact__ = "Jerome.Kieffer@terre-adelie.org"
__license__ = "GPLv3+"
__copyright__ = "Jérôme Kieffer"
__version__ = "15/02/2015"

import numpy
import logging
import os
import posixpath
import sys
from .fabioimage import FabioImage
logger = logging.getLogger("hdf5image")
if sys.version_info[0] < 3:
    bytes = str

try:
    import h5py
except ImportError:
    h5py = None
from .fabioutils import previous_filename, next_filename


class Hdf5Image(FabioImage):
    """
    FabIO image class for Images from an HDF file
    
    filename::dataset
    
    """
    def __init__(self, *arg, **kwargs):
        """
        Generic constructor
        """
        if not h5py:
            raise RuntimeError("fabio.Hdf5Image cannot be used without h5py. Please install h5py and restart")

        FabioImage.__init__(self, *arg, **kwargs)
        self.hdf5 = None
        self.dataset = None

    def read(self, fname, frame=None):
        """
        try to read image
        @param fname: filename::datasetpath
        """

        self.resetvals()
        if "::" not in fname:
            err = "the '::' separator in mandatory for HDF5 container, absent in %s" % fname
            logger.error(err)
            raise RuntimeError(err)
        filename, datapath = fname.split("::", 1)

        self.filename = filename
        if os.path.isfile(self.filename):
            self.hdf5 = h5py.File(self.filename, "r")
        else:
            error = "No such file or directory: %s" % self.filename
            logger.error(error)
            raise RuntimeError(error)
        try:
            self.dataset = self.hdf5[datapath]
        except Exception as err:
            logger.error("No such datapath %s in %s, %s", datapath, filename, err)
            raise
        if isinstance(self.dataset, h5py.Group) and ("data" in self.dataset):
            datapath = posixpath.join(datapath, "data")
            logger.warning("The actual dataset is ")
            self.dataset = self.dataset["data"]

        if self.dataset.ndim == 3:
            self.nframes = self.dataset.shape[0]
            if frame is not None:
                self.currentframe = int(frame)
            else:
                self.currentframe = 0
            self.data = self.dataset[self.currentframe, :, :]
        elif self.dataset.ndim == 2:
            self.data = self.dataset[:, :]
        else:
            err = "Only 2D and 3D datasets are supported by FabIO, here %sD" % self.dataset.ndim
            logger.error(err)
            raise RuntimeError(err)
        return self

    def write(self, fname, force_type=numpy.uint16):
        raise NotImplementedError("Write is not implemented")

    def getframe(self, num):
        """
        Returns a frame as a new FabioImage object
        @param num: frame number
        """
        if num < 0 or num > self.nframes:
            raise RuntimeError("Requested frame number %i is out of range [0, %i[ " % (num, self.nframes))
        # Do a deep copy of the header to make a new one
        frame = self.__class__(header=self.header)
        frame.hdf5 = self.hdf5
        frame.dataset = self.dataset
        frame.filename = self.filename
        frame.nframes = self.nframes
        frame.data = self.dataset[num, :, :]
        frame.currentframe = num
        return frame

    def next(self):
        """
        Get the next image in a series as a fabio image
        """
        if self.currentframe < (self.nframes - 1):
            return self.getframe(self.currentframe + 1)
        else:
            newobj = Hdf5Image()
            newobj.read(next_filename(self.filename))
            return newobj

    def previous(self):
        """
        Get the previous image in a series as a fabio image
        """
        if self.currentframe > 0:
            return self.getframe(self.currentframe - 1)
        else:
            newobj = Hdf5Image()
            newobj.read(previous_filename(self.filename))
            return newobj


hdf5image = Hdf5Image
