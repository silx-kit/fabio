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

hdf5:///filename?path#slice=[:,:,1]

"""
# Get ready for python3:
from __future__ import with_statement, print_function, division

__authors__ = ["Jérôme Kieffer"]
__contact__ = "Jerome.Kieffer@terre-adelie.org"
__license__ = "GPLv3+"
__copyright__ = "Jérôme Kieffer"
__version__ = "15/02/2015"

import numpy, logging, os, posixpath, sys, copy
from .fabioimage import FabioImage
logger = logging.getLogger("hdf5image")
if sys.version_info[0] < 3:
    bytes = str
    from urlparse import urlparse
else:
    from urllib.parse import  urlparse

try:
    import h5py
except ImportError:
    h5py = None
from .fabioutils import previous_filename, next_filename


class Hdf5Image(FabioImage):
    """
    FabIO image class for Images from an HDF file
    """
    def __init__(self, *arg, **kwargs):
        """
        Generic constructor
        """
        if not h5py:
            raise RuntimeError("fabio.Hdf5Image cannot be used without h5py. Please install h5py and restart")

        FabioImage.__init__(self, *arg, **kwargs)
        self.data = None
        self.header = self.check_header()
        self.dim1 = self.dim2 = 0
        self.m = self.maxval = self.stddev = self.minval = None
        self.header_keys = self.header.keys()
        self.bytecode = None
        self.hdf5 = None
        self.nframes = None
        self.url = tuple()
        self.main_dim = None

    def set_url(self, url):
        """
        set the url of the data
        """
        self.url = url

    def get_slice(self):
        if not self.url:
            return
        res = []
        if self.url.fragment.startswith("slice"):
            for idx, grp in enumerate(self.url.fragment[7:-1].split(",")):
                ssi = []
                if not ":" in grp:
                    self.main_dim = idx
                for i in grp.split(":"):
                    if i:
                        ssi.append(int(i))
                    else:
                        ssi.append(None)
                res.append(slice(*ssi))
        print(res)
        return tuple(res)

    def read(self, fname, frame=None):
        """
        try to read image
        @param fname: name of the file as hdf5:///filename?path#slice=[:,:,1]
        """

        self.resetvals()
        url = urlparse(fname)
        if not self.url:
            self.url = url
#        if frame:
#            self.hdf5_location.set_index(frame)
        self.filename = self.url.path
        if os.path.isfile(self.filename):
            self.hdf5 = h5py.File(self.filename, "r")
        else:
            error = "No such file or directory: %s" % self.filename
            logger.error(error)
            raise RuntimeError(error)
        self.ds = self.hdf5[self.url.query]
        if isinstance(self.ds, h5py.Group) and ("data" in self.ds):
            self.ds = self.ds["data"]

        if self.url.fragment:
            slices = self.get_slice()
            self.data = self.ds[self.get_slice()]
            self.nframes = self.ds.shape[self.main_dim]
        else:
            self.data = self.ds[:]
            self.nframes = 1
        self.dim2, self.dim1 = self.data.shape
        self.bytecode = str(self.data.dtype)
        return self

    def write(self, fname, force_type=numpy.uint16):
        raise NotImplementedError("Write is not implemented")

    def getframe(self, num):
        """
        Returns a frame as a new FabioImage object
        @param num: frame number
        """
        if num < 0 or num > self.nframes:
            raise RuntimeError("Requested frame number is out of range")
        # Do a deep copy of the header to make a new one
        frame = Hdf5Image(header=self.header.copy())
        frame.header_keys = self.header_keys[:]
        for key in ("dim1", "dim2", "nframes", "bytecode", "hdf5", "ds"):
            frame.__setattr__(key, self.__getattribute__(key))
        frame.hdf5_location = copy.deepcopy(self.hdf5_location)
        frame.hdf5_location.set_index(num)
        if self.hdf5_location.slice:
            self.data = self.ds[tuple(self.hdf5_location.slice)]
            self.nframes = self.ds.shape[self.hdf5_location.last_index]
        else:
            self.data = self.ds[:]
        return frame

    def next(self):
        """
        Get the next image in a series as a fabio image
        """
        if self.currentframe < (self.nframes - 1) and self.nframes > 1:
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
