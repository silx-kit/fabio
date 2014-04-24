#!/usr/bin/env python
# coding: utf-8

"""
HDF5 image for FabIO

Authors: Jerome Kieffer
email:  Jerome.Kieffer@terre-adelie.org

Specifications:
input should being the form:

hdf5://filename:path[slice]

"""
# Get ready for python3:
from __future__ import with_statement, print_function, division

__authors__ = ["Jérôme Kieffer"]
__contact__ = "Jerome.Kieffer@terre-adelie.org"
__license__ = "GPLv3+"
__copyright__ = "Jérôme Kieffer"
__version__ = "12 Nov 2013"

import numpy, logging, os, posixpath, sys, copy
from .fabioimage import fabioimage
logger = logging.getLogger("hdf5image")
if sys.version_info < (3.0):
    bytes = str

try:
    import h5py
except ImportError:
    h5py = None
from .fabioutils import previous_filename, next_filename

class HDF5location(object):
    """
    Handle URL like:

    hdf5://filename:path[slice]

    """
    def __init__(self, filename=None, h5path=None, slices=None, url=None):
        self.filename = filename
        if h5path:
            self.dataset = posixpath.abspath(h5path)
            self.group = posixpath.dirname(self.dataset)
        else:
            self.dataset = None
            self.group = None

        self.slice = copy.deepcopy(slices)
        self.last_index = None # where should I increment when next.
        if self.slice:
            for i, j  in enumerate(self.slice):
                if "__len__" in dir(j):
                    if ":" in j:
                        self.slice[i] = slice(None, None, 1)
                    else:
                        self.slice[i] = int(j)
                        self.last_index = i
                else:
                    self.slice[i] = int(j)
                    self.last_index = i

        if url is not None:
            self.parse(url)

    def __repr__(self):
        return "HDF5location: %s" % self.to_url()

    def parse(self, url):
        """
        Analyse a string of the form hdf5://filename:path[slice]

        @param url: string of form of an hdf5-url
        """
        if "[" in url:
            url, sslice = url.split("[", 1)
            sslice = sslice[:sslice.index("]")]
            slices = []
            for idx, i in enumerate(sslice.split(",")):
                if ":" in i:
                    s = slice(None, None, 1)
                else:
                    try:
                        s = int(i)
                        self.last_index = idx
                    except:
                        logger.error("unable to convert to integer for slice %s in %s" % (i, sslice))
                        s = slice(None, None, 1)
                slices.append(s)
            self.slice = slices
        else:
            self.slice = None
        col_split = url.split(":")
#        col_split
        self.dataset = posixpath.abspath(col_split[-1])
        col_split = col_split[:-1]
        self.group = posixpath.dirname(self.dataset)
        if col_split[0].lower() in ("hdf5", "h5"):
            col_split = col_split[1:]
        if col_split[0].startswith("//"):
            col_split[0] = col_split[0][2:]
        self.filename = ":".join(col_split)
        if not os.path.isfile(self.filename):
            logger.info("HDF5 filename does not exist: %s" % self.filename)

    def to_url(self):
        """
        convert an HDF5 locate into an URL
        """
        if (self.filename and self.dataset):
            url = "hdf5://%s:%s" % (self.filename, self.dataset)
        else:
            url = ""
        if self.slice:
            url += "["
            for i in self.slice:
                if type(i) == slice:
                    url += ":"
                else:
                    url += str(i)
                url += ","
            url = url[:-1] + "]"
        return url

    def set_index(self, idx):
        """
        Set the current frame to idx
        """
        if self.slice:
            self.slice[self.last_index] = idx
        else:
            raise RuntimeError("Changing slices is not allowed without slicing.")

class hdf5image(fabioimage):
    """
    FabIO image class for Images from an HDF file
    """
    def __init__(self, *arg, **kwargs):
        """
        Generic constructor
        """
        if not h5py:
            raise RuntimeError("fabio.hdf5image cannot be used without h5py. Please install h5py and restart")

        fabioimage.__init__(self, *arg, **kwargs)
        self.data = None
        self.header = {}
        self.dim1 = self.dim2 = 0
        self.m = self.maxval = self.stddev = self.minval = None
        self.header_keys = self.header.keys()
        self.bytecode = None
        self.hdf5 = None
        self.hdf5_location = None
        self.nframes = None


    def read(self, fname, frame=None):
        """
        try to read image
        @param fname: name of the file as hdf5://filename:path[slice]
        """

        self.resetvals()
        self.hdf5_location = HDF5location(url=fname)
        if frame:
            self.hdf5_location.set_index(frame)
        self.filename = self.hdf5_location.filename
        if os.path.isfile(self.filename):
            self.hdf5 = h5py.File(self.filename, "r")
        else:
            error = "No such file or directory: %s" % self.filename
            logger.error(error)
            raise RuntimeError(error)
        self.ds = self.hdf5[self.hdf5_location.dataset]
        if "Group" in self.ds.__class__.__name__:
            self.ds = self.ds["data"]
        if self.hdf5_location.slice:
            self.data = self.ds[tuple(self.hdf5_location.slice)]
            self.nframes = self.ds.shape[self.hdf5_location.last_index]
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
        Returns a frame as a new fabioimage object
        @param num: frame number
        """
        if num < 0 or num > self.nframes:
            raise RuntimeError("Requested frame number is out of range")
        # Do a deep copy of the header to make a new one
        frame = hdf5image(header=self.header.copy())
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
            newobj = hdf5image()
            newobj.read(next_filename(self.filename))
            return newobj

    def previous(self):
        """
        Get the previous image in a series as a fabio image
        """
        if self.currentframe > 0:
            return self.getframe(self.currentframe - 1)
        else:
            newobj = hdf5image()
            newobj.read(previous_filename(self.filename))
            return newobj
