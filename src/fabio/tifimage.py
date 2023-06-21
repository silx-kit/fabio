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

"""
FabIO class for dealing with TIFF images.
In facts wraps TiffIO from V. Armando Solé (available in PyMca) or falls back to PIL

Authors:
........
* Henning O. Sorensen & Erik Knudsen:
  Center for Fundamental Research: Metal Structures in Four Dimensions;
  Risoe National Laboratory;
  Frederiksborgvej 399;
  DK-4000 Roskilde;
  email:erik.knudsen@risoe.dk
* Jérôme Kieffer:
  European Synchrotron Radiation Facility;
  Grenoble (France)
"""

__authors__ = ["Jérôme Kieffer", "Henning O. Sorensen", "Erik Knudsen"]
__date__ = "03/04/2020"
__license__ = "MIT"
__copyright__ = "ESRF, Grenoble & Risoe National Laboratory"
__status__ = "stable"

import time
import logging
logger = logging.getLogger(__name__)

try:
    import PIL
except ImportError:
    PIL = None

import numpy
from .utils import pilutils
from . import fabioimage
from . import TiffIO

_USE_TIFFIO = True
"""Uses TiffIO library if available"""

_USE_PIL = True
"""Uses PIL library if available"""


class TiffFrame(fabioimage.FabioFrame):
    """Frame container for TIFF format"""

    def __init__(self, data, tiff_header):
        super(TiffFrame, self).__init__(data, tiff_header)
        # also expose the tiff header as 'tiff header' attribute
        self.tiff_header = tiff_header


class TifImage(fabioimage.FabioImage):
    """
    Images in TIF format
    Wraps TiffIO
    """
    DESCRIPTION = "Tagged image file format"

    DEFAULT_EXTENSIONS = ["tif", "tiff"]

    _need_a_seek_to_read = True

    def __init__(self, *args, **kwds):
        """ Tifimage constructor adds an nbits member attribute """
        self.nbits = None
        fabioimage.FabioImage.__init__(self, *args, **kwds)
        self._tiffio = None
        self.lib = None

    def _readheader(self, infile):
        """
        Try to read Tiff images header...
        """
        header = numpy.frombuffer(infile.read(64), numpy.uint16)
        # TODO: this values dim1/dim2 looks to be wrong
        dim1 = int(header[9])
        dim2 = int(header[15])
        self._shape = dim2, dim1
        # nbits is not a FabioImage attribute...
        self.nbits = int(header[21])  # number of bits

    def _create_frame(self, image_data, tiff_header):
        """Create exposed data from TIFF information"""
        return TiffFrame(image_data, tiff_header)

    def _read_header_from_pil(self, image):
        header = self.check_header()
        for num, name in TiffIO.TAG_ID.items():
            if num in image.tag:
                name = name[0].lower() + name[1:]
                value = image.tag[num]
                # For some PIL version the tag content is a tuple
                if isinstance(value, tuple) and len(value) == 1:
                    value = value[0]
                header[name] = value

        return header

    def _read_with_tiffio(self, infile):
        tiffIO = TiffIO.TiffIO(infile)
        self._nframes = tiffIO.getNumberOfImages()
        if self.nframes > 0:
            # No support for now of multi-frame tiff images
            header = tiffIO.getInfo(0)
            data = tiffIO.getData(0)
            frame = self._create_frame(data, header)
            self.header = frame.header
            self.data = frame.data
        self._tiffio = tiffIO
        if self.data.ndim == 2:
            self._shape = None
        elif self.data.ndim == 3:
            logger.warning("Third dimension is the color")
            self._shape = None
        else:
            logger.warning("dataset has %s dimensions (%s), check for errors !!!!", self.data.ndim, self.data.shape)
        self.lib = "TiffIO"

    def _read_with_pil(self, infile):
        pilimage = PIL.Image.open(infile)
        header = self._read_header_from_pil(pilimage)
        data = pilutils.get_numpy_array(pilimage)
        frame = self._create_frame(data, header)
        self.header = frame.header
        self.data = frame.data
        self._shape = None
        self.lib = "PIL"

    def read(self, fname, frame=None):
        """
        Wrapper for TiffIO.
        """
        infile = self._open(fname, "rb")
        self._readheader(infile)
        self.lib = None
        infile.seek(0)

        if _USE_TIFFIO:
            try:
                self._read_with_tiffio(infile)
            except Exception as error:
                logger.warning("Unable to read %s with TiffIO due to %s, trying PIL", fname, error)
                logger.debug("Backtrace", exc_info=True)
                infile.seek(0)

        if self.lib is None:
            if _USE_PIL and PIL is not None:
                try:
                    self._read_with_pil(infile)
                except Exception as error:
                    logger.error("Error in opening %s with PIL: %s", fname, error)
                    logger.debug("Backtrace", exc_info=True)
                    if infile.closed:
                        infile = self._open(fname, "rb")
                    else:
                        infile.close()

        if self.lib is None:
            logger.error("Error in opening %s: no tiff reader managed to read the file.", fname)

        self.resetvals()
        return self

    def write(self, fname):
        """
        Overrides the FabioImage.write method and provides a simple TIFF image writer.

        :param str fname: name of the file to save the image to
        """
        with TiffIO.TiffIO(fname, mode="w") as tiff_file:
            tiff_file.writeImage(self.data,
                                 info=self.header,
                                 software="fabio.tifimage",
                                 date=time.ctime())

    def close(self):
        if self._tiffio is not None:
            self._tiffio.close()
            self._tiffio = None
        super(TifImage, self).close()

    def _get_frame(self, num):
        """Inherited function returning a FabioFrame"""
        if 0 <= num < self.nframes:
            frame = self.getframe(num)
            frame._set_container(self, num)
            frame._set_file_container(self, num)
            return frame
        raise IndexError("getframe out of range")

    def getframe(self, num):
        """Returns the frame `num`.

        This frame is not cached on the image structure.
        """
        if self._tiffio is None:
            raise NotImplementedError("getframe is only implemented for TiffIO lib")

        if 0 <= num < self.nframes:
            image_data = self._tiffio.getData(num)
            tiff_header = self._tiffio.getInfo(num)
            return self._create_frame(image_data, tiff_header)
        raise Exception("getframe out of range")


tifimage = TifImage
