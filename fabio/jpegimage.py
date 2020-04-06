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

__authors__ = ["Valentin Valls"]
__date__ = "03/04/2020"
__license__ = "MIT"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__status__ = "stable"

import logging
logger = logging.getLogger(__name__)

try:
    from PIL import Image
except ImportError:
    Image = None

from .fabioimage import FabioImage
from .utils import pilutils

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

    DEFAULT_EXTENSIONS = ["jpg", "jpeg"]

    RESERVED_HEADER_KEYS = JPEG_RESERVED_HEADER_KEYS

    _need_a_seek_to_read = True

    def __init__(self, *args, **kwds):
        """ Tifimage constructor adds an nbits member attribute """
        self.nbits = None
        FabioImage.__init__(self, *args, **kwds)

    def _readWithPil(self, filename, infile):
        try:
            infile.seek(0)
            pilimage = Image.open(infile)
        except Exception:
            pilimage = None
            infile.seek(0)
            raise IOError("Error in opening %s with PIL" % filename)

        data = pilutils.get_numpy_array(pilimage)
        self.data = data

        if pilimage and pilimage.info:
            for k, v in pilimage.info.items():
                self.header[k] = v

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
