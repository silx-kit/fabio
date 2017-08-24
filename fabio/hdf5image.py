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


"""HDF5 image for FabIO

Authors: Jerome Kieffer
email:  Jerome.Kieffer@terre-adelie.org

Specifications:
input should being the form:

filename::path

Only supports ndim=2 or 3 (exposed as a stack of images
"""
# Get ready for python3:
from __future__ import with_statement, print_function, division

__authors__ = ["Jérôme Kieffer"]
__contact__ = "Jerome.Kieffer@terre-adelie.org"
__license__ = "MIT"
__copyright__ = "Jérôme Kieffer"
__date__ = "24/07/2017"

import logging
import os
import posixpath
import sys
from .fabioimage import FabioImage
logger = logging.getLogger(__name__)
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

    DESCRIPTION = "Hierarchical Data Format HDF5 flat reader"

    DEFAULT_EXTENTIONS = ["h5"]

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
        :param fname: filename::datasetpath
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

        # ndim does not exist for external links ?
        ndim = len(self.dataset.shape)
        if ndim == 3:
            self.nframes = self.dataset.shape[0]
            if frame is not None:
                self.currentframe = int(frame)
            else:
                self.currentframe = 0
            self.data = self.dataset[self.currentframe, :, :]
        elif ndim == 2:
            self.data = self.dataset[:, :]
        else:
            err = "Only 2D and 3D datasets are supported by FabIO, here %sD" % self.dataset.ndim
            logger.error(err)
            raise RuntimeError(err)
        return self

    def getframe(self, num):
        """
        Returns a frame as a new FabioImage object
        :param num: frame number
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
