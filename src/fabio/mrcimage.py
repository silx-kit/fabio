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

"""MRC image for FabIO

Authors: Jerome Kieffer
email:  Jerome.Kieffer@terre-adelie.org

Specifications from:
http://ami.scripps.edu/software/mrctools/mrc_specification.php
New version on:
https://www.ccpem.ac.uk/mrc_format/mrc_format.php
https://www.fei-software-center.com/tem-apps/MRC-2014-Specifications/
"""

__authors__ = ["Jérôme Kieffer"]
__contact__ = "Jerome.Kieffer@terre-adelie.org"
__license__ = "MIT"
__copyright__ = "Jérôme Kieffer"
__date__ = "23/04/2021"

import logging
import numpy

from .fabioimage import FabioImage
from .fabioutils import previous_filename, next_filename

logger = logging.getLogger(__name__)


class MrcImage(FabioImage):
    """
    FabIO image class for Images from a mrc image stack
    """

    DESCRIPTION = "Medical Research Council file format for 3D electron density and 2D images"

    DEFAULT_EXTENSIONS = ["mrc", "map", "fei"]

    KEYS = ("NX", "NY", "NZ", "MODE", "NXSTART", "NYSTART", "NZSTART",
            "MX", "MY", "MZ", "CELL_A", "CELL_B", "CELL_C",
            "CELL_ALPHA", "CELL_BETA", "CELL_GAMMA",
            "MAPC", "MAPR", "MAPS", "DMIN", "DMAX", "DMEAN", "ISPG", "NSYMBT",
            "EXTRA", "ORIGIN", "MAP", "MACHST", "RMS", "NLABL")

    _MODE_TO_DTYPE = {
        0: numpy.int8,
        1: numpy.int16,
        2: numpy.float32,
        3: numpy.complex64,
        4: numpy.complex64,
        6: numpy.uint16
    }

    def _readheader(self, infile):
        """
        Read and decode the header of an image:

        :param infile: Opened python file (can be stringIO or bipped file)
        """
        # list of header key to keep the order (when writing)
        self.header = self.check_header()

        # header is composed of 56-int32 plus 10x80char lines
        int_block = numpy.frombuffer(infile.read(56 * 4), dtype=numpy.int32)
        for key, value in zip(self.KEYS, int_block):
            self.header[key] = value
        # convert some headers ...
        self.header["MAP"] = self.header["MAP"].tobytes().decode()
        if self.header["MAP"][:3] not in ('MAP ', 'FEI'):
            logger.info("Expected 'MAP ', got %s", self.header["MAP"])

        for i in range(10):
            label = "LABEL_%02i" % i
            self.header[label] = infile.read(80).decode().strip()

        # Read extended header
        self.header["extended"] = infile.read(self.header["NSYMBT"])

        dim1 = int(self.header["NX"])
        dim2 = int(self.header["NY"])
        self._shape = dim2, dim1

        self._nframes = self.header["NZ"]
        mode = self.header["MODE"]
        if mode not in self._MODE_TO_DTYPE:
            raise IOError("Mode %s unsupported" % mode)
        dtype = numpy.dtype(self._MODE_TO_DTYPE[mode])
        self._dtype = dtype
        self.imagesize = dim1 * dim2 * dtype.itemsize

    def read(self, fname, frame=None):
        """
        try to read image
        :param fname: name of the file
        :param frame:
        """

        self.resetvals()
        self.sequencefilename = fname
        self.currentframe = frame or 0

        with self._open(fname) as infile:
            self._readheader(infile)
            self._readframe(infile, self.currentframe)
        return self

    def _calc_offset(self, frame):
        """
        Calculate the frame position in the file

        :param frame: frame number
        """
        assert frame < self.nframes
        return 1024 + self.header["NSYMBT"] + frame * self.imagesize

    def _makeframename(self):
        self.filename = "%s$%04d" % (self.sequencefilename,
                                     self.currentframe)

    def _readframe(self, infile, img_num):
        """
        Read a frame an populate data
        :param infile: opened file
        :param img_num: frame number (int)
        """
        if (img_num > self.nframes or img_num < 0):
            raise RuntimeError("Requested frame number is out of range")
        infile.seek(self._calc_offset(img_num), 0)
        data_buffer = infile.read(self.imagesize)
        data = numpy.frombuffer(data_buffer, self._dtype).copy()
        data.shape = self._shape
        self.data = data
        self._shape = None
        self._dtype = None
        self.currentframe = int(img_num)
        self._makeframename()

    def getframe(self, num):
        """
        Returns a frame as a new FabioImage object
        :param num: frame number
        """
        if num < 0 or num > self.nframes:
            raise RuntimeError("Requested frame number is out of range")
        # Do a deep copy of the header to make a new one
        frame = MrcImage(header=self.header.copy())
        for key in ("dim1", "dim2", "nframes", "bytecode", "imagesize", "sequencefilename"):
            frame.__setattr__(key, self.__getattribute__(key))
        with frame._open(self.sequencefilename, "rb") as infile:
            frame._readframe(infile, num)
        return frame

    def next(self):
        """
        Get the next image in a series as a fabio image
        """
        if self.currentframe < (self.nframes - 1) and self.nframes > 1:
            return self.getframe(self.currentframe + 1)
        else:
            newobj = MrcImage()
            newobj.read(next_filename(self.sequencefilename))
            return newobj

    def previous(self):
        """
        Get the previous image in a series as a fabio image
        """
        if self.currentframe > 0:
            return self.getframe(self.currentframe - 1)
        else:
            newobj = MrcImage()
            newobj.read(previous_filename(
                self.sequencefilename))
            return newobj


mrcimage = MrcImage
