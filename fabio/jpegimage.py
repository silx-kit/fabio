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
FabIO class for dealing with JPEG images.
"""

from __future__ import with_statement, print_function, division

__authors__ = ["Valentin Valls"]
__date__ = "27/07/2017"
__license__ = "MIT"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__status__ = "stable"

import logging
logger = logging.getLogger(__name__)
import numpy

try:
    from PIL import Image
except ImportError:
    Image = None

from .fabioimage import FabioImage


PIL_TO_NUMPY = {
    "I;8": numpy.uint8,
    "I;16": numpy.uint16,
    "I;16B": numpy.uint16,    # big endian
    "I;16L": numpy.uint16,    # little endian
    "I;32": numpy.uint32,
    "I;32L": numpy.uint32,    # little endian
    "I;32B": numpy.uint32,    # big endian
    "F;32F": numpy.float32,
    "F;32BF": numpy.float32,  # big endian
    "F;64F": numpy.float64,
    "F;64BF": numpy.float64,  # big endian
    "F": numpy.float32,
    "1": numpy.bool,
    "I": numpy.int32,
    "L": numpy.uint8,
}


# List of reserved keys reached from
# http://pillow.readthedocs.io/en/3.4.x/handbook/image-file-formats.html#jpeg
JPEG_RESERVED_HEADER_KEYS = [
    "jfif",
    "jfif_version",
    "jfif_density",
    "jfif_unit",
    "dpi",
    "adobe",
    "adobe_transform",
    "progression",
    "icc_profile",
    "exif",
    "quality",
    "optimize",
    "progressive",
    "dpi",
    "exif",
    "subsampling",
    "qtables"
]


class JpegImage(FabioImage):
    """
    Images in JPEG format using PIL
    """
    DESCRIPTION = "JPEG format"

    DEFAULT_EXTENTIONS = ["jpg", "jpeg"]

    RESERVED_HEADER_KEYS = JPEG_RESERVED_HEADER_KEYS

    _need_a_seek_to_read = True

    def __init__(self, *args, **kwds):
        """ Tifimage constructor adds an nbits member attribute """
        self.nbits = None
        FabioImage.__init__(self, *args, **kwds)

    def _readWithPil(self, filename, infile):
        try:
            infile.seek(0)
            self.pilimage = Image.open(infile)
        except Exception:
            infile.seek(0)
            raise IOError("Error in opening %s with PIL" % filename)

        dim1, dim2 = self.pilimage.size
        if self.pilimage.mode in PIL_TO_NUMPY:
            dtype = PIL_TO_NUMPY[self.pilimage.mode]
            pilimage = self.pilimage
        else:
            dtype = numpy.float32
            pilimage = self.pilimage.convert("F")
        try:
            data = numpy.asarray(pilimage, dtype)
        except:
            # PIL does not support buffer interface (yet)
            if hasattr(pilimage, "tobytes"):
                data = numpy.fromstring(pilimage.tobytes(), dtype=dtype)
            else:
                data = numpy.fromstring(pilimage.tostring(), dtype=dtype)
            # byteswap ?
            if numpy.dtype(dtype).itemsize > 1:
                need_swap = False
                need_swap |= numpy.little_endian and "B" in self.pilimage.mode
                need_swap |= not numpy.little_endian and self.pilimage.mode.endswith("L")
                if need_swap:
                    data.byteswap(True)

        if self.pilimage and self.pilimage.info:
            for k, v in self.pilimage.info.items():
                self.header[k] = v

        self.data = data.reshape((dim2, dim1))

    def read(self, filename, frame=None):
        infile = self._open(filename, "rb")
        self.data = None

        if Image is not None:
            self._readWithPil(filename, infile)

        if self.data is None:
            infile.seek(0)
            raise IOError("Error in opening %s." % filename)

        self.resetvals()
        return self


jpegimage = JpegImage
