# coding: utf-8
#
#    Project: FabIO X-ray image reader
#
#    Copyright (C) 2010-2016 European Synchrotron Radiation Facility
#                       Grenoble, France
#
#    Copyright (C) 2019      Synchrotron-SOLEIL
#                            Gif-sur-Yvette, France
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


"""Soleil HDF5 image for FabIO

Authors: Jerome Kieffer, Picca Frédéric-Emmanuel
email:  Jerome.Kieffer@terre-adelie.org, picca@synchrotron-soleil.fr

Specifications:
input should being the form:

filename

Only supports ndim=2 or 3 (exposed as a stack of images)
"""

from __future__ import with_statement, print_function, division

__authors__ = ["Jérôme Kieffer", "Picca Frédéric-Emmanuel"]
__contact__ = "Jerome.Kieffer@terre-adelie.org"
__license__ = "MIT"
__copyright__ = "Jérôme Kieffer"
__date__ = "01/03/2019"

import logging

logger = logging.getLogger(__name__)

from collections import namedtuple
from functools import partial

try:
    import h5py
    from h5py import Dataset, File
except ImportError:
    h5py = None

from fabio.fabioimage import FabioFrame, FabioImage
from .fabioutils import previous_filename, next_filename

# Generic hdf5 access types.

DatasetPathContains = namedtuple("DatasetPathContains", "path")
DatasetPathWithAttribute = namedtuple("DatasetPathWithAttribute", "attribute value")

def _v_attrs(attribute, value, _name, obj):
    """extract all the images and accumulate them in the acc variable"""
    if isinstance(obj, Dataset):
        if attribute in obj.attrs and obj.attrs[attribute] == value:
            return obj


def _v_item(key, name, obj):
    if key in name:
        return obj


def get_dataset(h5file, path):
    res = None
    if isinstance(path, DatasetPathContains):
        res = h5file.visititems(partial(_v_item, path.path))
    elif isinstance(path, DatasetPathWithAttribute):
        res = h5file.visititems(partial(_v_attrs,
                                        path.attribute, path.value))
    return res


class SoleilFrame(FabioFrame):
    """Identify a slice of dataset from an HDF5 file"""

    def __init__(self, soleil_image, frame_num):
        if not isinstance(soleil_image, SoleilImage):
            raise TypeError("Expected class {SoleilImage}".format(SoleilImage))
        data = soleil_image.dataset[frame_num, :, :]
        super(SoleilFrame, self).__init__(data=data, header=soleil_image.header)
        self.hdf5 = soleil_image.hdf5
        self.dataset = soleil_image.dataset
        self.filename = soleil_image.filename
        self._nframes = soleil_image.nframes
        self.header = soleil_image.header
        self.currentframe = frame_num


class SoleilImage(FabioImage):
    """
    FabIO image class for Images from an Soleil HDF file

    filename::dataset
    """

    DESCRIPTION = "Soleil Hierarchical Data Format HDF5 flat reader"

    DEFAULT_EXTENSIONS = ["nxs", "h5"]

    def __init__(self, *arg, **kwargs):
        if not h5py:
            raise RuntimeError("fabio.SoleilImage cannot be used without h5py. Please install h5py and restart")
        super(SoleilImage, self).__init__(*arg, **kwargs)
        self.hdf5 = None
        self.dataset = None

    def read(self, filename, frame=None):
        """
        try to read image
        :param fname: filename
        """
        self.resetvals()

        path = DatasetPathWithAttribute("interpretation", b"image")
        self.filename = filename
        self.hdf5 = File(self.filename, "r")
        self.dataset = get_dataset(self.hdf5, path)

        # ndim does not exist for external links ?
        ndim = len(self.dataset.shape)
        if ndim == 3:
            self._nframes = self.dataset.shape[0]
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
        return SoleilFrame(self, num)

    def next(self):
        """
        Get the next image in a series as a fabio image
        """
        if self.currentframe < (self.nframes - 1):
            return self.getframe(self.currentframe + 1)
        else:
            newobj = SoleilImage()
            newobj.read(next_filename(self.filename))
            return newobj

    def previous(self):
        """
        Get the previous image in a series as a fabio image
        """
        if self.currentframe > 0:
            return self.getframe(self.currentframe - 1)
        else:
            newobj = SoleilImage()
            newobj.read(previous_filename(self.filename))
            return newobj

    def close(self):
        if self.hdf5 is not None:
            self.hdf5.close()
            self.dataset = None
