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
FabIO class for dealing with JPEG 2000 images.
"""

from __future__ import with_statement, print_function, division

__authors__ = ["Valentin Valls"]
__date__ = "19/08/2019"
__license__ = "MIT"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__status__ = "stable"

import logging
logger = logging.getLogger(__name__)

try:
    import PIL
except ImportError:
    PIL = None

try:
    import glymur
except ImportError:
    glymur = None


from .fabioimage import FabioImage
from .fabioutils import OrderedDict
from .utils import pilutils


class Jpeg2KImage(FabioImage):
    """
    Images in JPEG 2000 format.

    It uses PIL or glymur libraries.
    """
    DESCRIPTION = "JPEG 2000 format"

    DEFAULT_EXTENSIONS = ["jp2", "jpx", "j2k", "jpf", "jpg2"]

    _need_a_seek_to_read = True

    def __init__(self, *args, **kwds):
        """ Tifimage constructor adds an nbits member attribute """
        self.nbits = None
        FabioImage.__init__(self, *args, **kwds)
        self.lib = ""

        self._decoders = OrderedDict()
        if PIL is not None:
            self._decoders["PIL"] = self._readWithPil
        if glymur is not None:
            self._decoders["glymur"] = self._readWithGlymur

    def _readWithPil(self, filename, infile):
        """Read data using PIL"""
        pilimage = PIL.Image.open(infile)
        data = pilutils.get_numpy_array(pilimage)
        self.data = data

        if pilimage and pilimage.info:
            for k, v in pilimage.info.items():
                self.header[k] = v

    def _loadGlymurImage(self, filename, infile):
        """
        Hack to use Glymur with Python file object

        This code was tested with all release 0.8.x
        """
        # image = glymur.Jp2k(filename)
        if glymur.__version__.startswith("0.7."):
            image = glymur.Jp2k(filename=filename)
        elif glymur.__version__.startswith("0.8."):
            # inject a shape  to avoid calling the read function
            image = glymur.Jp2k(filename=filename, shape=(1, 1))
        else:
            raise IOError("Glymur version %s is not supported" % glymur.__version__)

        # Move to the end of the file to know the size
        infile.seek(0, 2)
        length = infile.tell()
        infile.seek(0)

        # initialize what it should already be done
        image.length = length
        image._shape = None
        # It is not the only one format supported by Glymur
        # but it is a simplification
        image._codec_format = glymur.lib.openjp2.CODEC_JP2

        # parse the data
        image.box = image.parse_superbox(infile)
        try:
            image._validate()
        except Exception:
            logger.debug("Backtrace", exc_info=True)
            raise IOError("File %s is not a valid format" % filename)

        # Now the image can be used normaly
        return image

    def _readWithGlymur(self, filename, infile):
        """Read data using Glymur"""
        image = self._loadGlymurImage(filename, infile)
        self.data = image.read()

    def read(self, filename, frame=None):
        infile = self._open(filename, "rb")
        self.data = None

        for name, read in self._decoders.items():
            try:
                infile.seek(0)
                read(filename, infile)
                self.lib = name
                break

            except IOError as e:
                self.data = None
                self.header = OrderedDict()
                logger.debug("Error while using %s library: %s" % (name, e), exc_info=True)

        if self.data is None:
            infile.seek(0)
            raise IOError("No decoder available for the file %s." % filename)
        self.resetvals()
        return self


jpeg2kimage = Jpeg2KImage
