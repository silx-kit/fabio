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
"""
# Get ready for python3:
from __future__ import with_statement, print_function

__authors__ = ["Jérôme Kieffer"]
__contact__ = "Jerome.Kieffer@terre-adelie.org"
__license__ = "MIT"
__copyright__ = "Jérôme Kieffer"
__version__ = "29 Oct 2013"

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
        if self.header["MAP"] != 542130509:
            logger.info("Expected 'MAP ', got %s", self.header["MAP"].tostring())

        for i in range(10):
            label = "LABEL_%02i" % i
            self.header[label] = infile.read(80).strip()
        self.dim1 = self.header["NX"]
        self.dim2 = self.header["NY"]
        self.nframes = self.header["NZ"]
        mode = self.header["MODE"]
        if mode == 0:
            self.bytecode = numpy.int8
        elif mode == 1:
            self.bytecode = numpy.int16
        elif mode == 2:
            self.bytecode = numpy.float32
        elif mode == 3:
            self.bytecode = numpy.complex64
        elif mode == 4:
            self.bytecode = numpy.complex64
        elif mode == 6:
            self.bytecode = numpy.uint16

        self.imagesize = int(self.dim1) * self.dim2 * numpy.dtype(self.bytecode).itemsize

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
        return 1024 + frame * self.imagesize

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
        data = numpy.frombuffer(infile.read(self.imagesize), self.bytecode).copy()
        self.data = data.reshape((self.dim2, self.dim1))
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
