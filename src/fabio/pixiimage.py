# coding: utf-8
#
#    Project: X-ray image reader
#             https://github.com/silx-kit/fabio
#
#
#    Copyright (C) European Synchrotron Radiation Facility, Grenoble, France
#
#    Principal author:       Jérôme Kieffer (Jerome.Kieffer@ESRF.eu)
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
# THE SOFTWARE

"""
File format to read images from PiXIrad PCDs manufactured by Pixirad Imaging
Counters SRL (http://www.pixirad.com/)

Author: Jon Wright, ESRF.
"""

__authors__ = ["Jon Wright", "Jérôme Kieffer"]
__contact__ = "wright@esrf.fr"
__license__ = "MIT"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__date__ = "03/04/2020"

import numpy
import os
import logging

logger = logging.getLogger(__name__)

from . import fabioimage
from .fabioutils import previous_filename, next_filename


class PixiImage(fabioimage.FabioImage):

    DESCRIPTION = "Pixi file format"

    DEFAULT_EXTENSIONS = []

    _need_a_seek_to_read = True

    _IMAGE_WIDTH = 476
    _IMAGE_HEIGHT = 512
    _MAGIC_SIZE = 4
    _HEADER_SIZE = 24
    _PIXEL_DEPTH = 2
    """Each pixel is stored as UINT16"""
    _PIXEL_COUNT = _IMAGE_WIDTH * _IMAGE_HEIGHT
    _IMAGE_SIZE = _PIXEL_COUNT * _PIXEL_DEPTH
    _FRAME_SIZE = _HEADER_SIZE + _IMAGE_SIZE

    def _readheader(self, infile):
        infile.seek(0)
        self.header = self.check_header()
        byt = infile.read(4)
        framesize = numpy.frombuffer(byt, numpy.int32)
        if framesize * 2 == self._FRAME_SIZE - self._MAGIC_SIZE:
            self.header['framesize'] = framesize
            self.header['width'] = self._IMAGE_WIDTH
            self.header['height'] = self._IMAGE_HEIGHT
            self.header['offset'] = self._HEADER_SIZE
        else:
            logger.warning("Bad framesize: %s", framesize)
            raise Exception("Bad framesize")

    def read(self, fname, frame=None):
        if frame is None:
            frame = 0
        self.header = self.check_header()
        self.resetvals()
        with self._open(fname, "rb") as infile:
            self.sequencefilename = fname.rsplit("$", 1)[0]
            self._readheader(infile)
            self._nframes = os.path.getsize(fname) // self._FRAME_SIZE
            self._readframe(infile, frame)
        # infile.close()
        return self

    def _get_frame(self, num):
        """Inherited function returning a FabioFrame"""
        if num < 0:
            raise IndexError("Requested frame id:%d out of bound" % num)
        if num >= self.nframes:
            raise IndexError("Requested frame id:%d out of bound" % num)

        newheader = {}
        for k in self.header.keys():
            newheader[k] = self.header[k]
        with self._open(self.filename, "rb") as infile:
            data = self._readdata(infile, num)
        frame = fabioimage.FabioFrame(data=data, header=newheader)
        frame._set_container(self, num)
        frame._set_file_container(self, num)
        return frame

    def _make_filename(self, img_num):
        self.currentframe = int(img_num)
        if self.nframes == 1:
            self.filename = "%s$%04d" % (self.sequencefilename,
                                         self.currentframe)

    def _readdata(self, filepointer, img_num):
        if (img_num >= self.nframes or img_num < 0):
            raise Exception("Bad image number")
        imgstart = self.header['offset'] + img_num * self._FRAME_SIZE
        filepointer.seek(imgstart, 0)
        data = numpy.frombuffer(filepointer.read(self._IMAGE_SIZE),
                                numpy.uint16).copy()
        data.shape = self.header['height'], self.header['width']
        return data

    def _readframe(self, filepointer, img_num):
        data = self._readdata(filepointer, img_num)
        self.data = data
        self._shape = None

    def getframe(self, num):
        """
        Returns a frame as a new FabioImage object
        """
        if num < 0:
            raise Exception("Requested frame number is out of range")
        # Do a deep copy of the header to make a new one
        newheader = {}
        for k in self.header.keys():
            newheader[k] = self.header[k]
        frame = PixiImage(header=newheader)
        frame._nframes = self.nframes
        frame.filename = self.filename
        frame.sequencefilename = self.sequencefilename
        frame._make_filename(num)
        with frame._open(frame.filename, "rb") as infile:
            if frame.nframes == 1:
                num = 0
            frame._readframe(infile, num)
        return frame

    def next(self):
        """
        Get the next image in a series as a fabio image
        """
        if self.currentframe < (self.nframes - 1) and self.nframes > 1:
            return self.getframe(self.currentframe + 1)
        else:
            newobj = PixiImage()
            newobj.read(next_filename(
                self.sequencefilename))
            return newobj

    def previous(self):
        """
        Get the previous image in a series as a fabio image
        """
        if self.currentframe > 0:
            return self.getframe(self.currentframe - 1)
        else:
            newobj = PixiImage()
            newobj.read(previous_filename(
                self.sequencefilename))
            return newobj


pixiimage = PixiImage
