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
Author: Jon Wright, ESRF.
"""
# Get ready for python3:
from __future__ import with_statement, print_function

__authors__ = ["Jon Wright", "Jérôme Kieffer"]
__contact__ = "wright@esrf.fr"
__license__ = "MIT"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__date__ = "25/06/2018"

import numpy
import os
import logging

logger = logging.getLogger(__name__)

from .fabioimage import FabioImage
from .fabioutils import previous_filename, next_filename


class PixiImage(FabioImage):

    DESCRIPTION = "Pixi file format"

    DEFAULT_EXTENSIONS = []

    _need_a_seek_to_read = True

    def _readheader(self, infile):
        infile.seek(0)
        self.header = self.check_header()
        byt = infile.read(4)
        framesize = numpy.frombuffer(byt, numpy.int32)
        if framesize == 243722:
            # life is good
            width = 476
            height = 512
            offset = 24
            self.header['framesize'] = framesize
            self.header['width'] = width
            self.header['height'] = height
            self.header['offset'] = offset
        else:
            logger.warning("Pixiimage, bad framesize: %s", framesize)
            raise

    def read(self, fname, frame=None):
        if frame is None:
            frame = 0
        self.header = self.check_header()
        self.resetvals()
        with self._open(fname, "rb") as infile:
            self.sequencefilename = fname
            self._readheader(infile)
            self.nframes = os.path.getsize(fname) / 487448
            self._readframe(infile, frame)
        # infile.close()
        return self

    def _makeframename(self):
        self.filename = "%s$%04d" % (self.sequencefilename,
                                     self.currentframe)

    def _readframe(self, filepointer, img_num):
        if (img_num > self.nframes or img_num < 0):
            raise Exception("Bad image number")
        imgstart = self.header['offset'] + img_num * (512 * 476 * 2 + 24)
        filepointer.seek(imgstart, 0)
        self.data = numpy.frombuffer(filepointer.read(512 * 476 * 2),
                                     numpy.uint16).copy()
        self.data.shape = self.header['height'], self.header['width']
        self.dim2, self.dim1 = self.data.shape
        self.currentframe = int(img_num)
        self._makeframename()

    def getframe(self, num):
        """
        Returns a frame as a new FabioImage object
        """
        if num < 0 or num > self.nframes:
            raise Exception("Requested frame number is out of range")
        # Do a deep copy of the header to make a new one
        newheader = {}
        for k in self.header.keys():
            newheader[k] = self.header[k]
        frame = pixiimage(header=newheader)
        frame.nframes = self.nframes
        frame.sequencefilename = self.sequencefilename
        infile = frame._open(self.sequencefilename, "rb")
        frame._readframe(infile, num)
        infile.close()
        return frame

    def next(self):
        """
        Get the next image in a series as a fabio image
        """
        if self.currentframe < (self.nframes - 1) and self.nframes > 1:
            return self.getframe(self.currentframe + 1)
        else:
            newobj = pixiimage()
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
            newobj = pixiimage()
            newobj.read(previous_filename(
                self.sequencefilename))
            return newobj


pixiimage = PixiImage


def demo(fname):
    i = PixiImage()
    i.read(fname)
    import pylab
    pylab.imshow(numpy.log(i.data))
    print("%s\t%s\t%s\t%s" % (i.filename, i.data.max(), i.data.min(), i.data.mean()))
    pylab.title(i.filename)
    pylab.show()
    while 1:
        i = i.next()
        pylab.imshow(numpy.log(i.data))
        pylab.title(i.filename)
        pylab.show()
        raw_input()


if __name__ == "__main__":
    import sys
    demo(sys.argv[1])
