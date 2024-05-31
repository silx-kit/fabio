# coding: utf-8
#
#    Project: X-ray image reader
#             https://github.com/silx-kit/fabio
#
#    Copyright (C) European Synchrotron Radiation Facility, Grenoble, France
#
#  Permission is hereby granted, free of charge, to any person
#  obtaining a copy of this software and associated documentation files
#  (the "Software"), to deal in the Software without restriction,
#  including without limitation the rights to use, copy, modify, merge,
#  publish, distribute, sublicense, and/or sell copies of the Software,
#  and to permit persons to whom the Software is furnished to do so,
#  subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be
#  included in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
#  OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#  NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#  HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
#  WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#  OTHER DEALINGS IN THE SOFTWARE.

"""Template for FabIO image reader

This is a template for adding new file formats to FabIO

We hope it will be relatively easy to add new file formats to fabio in the
future.
The basic idea is the following:

1) inherit from FabioImage overriding the methods _readheader, read and optionally write.
   Name your new module XXXimage where XXX means something (eg tifimage).

2) readheader fills in a dictionary of "name":"value" pairs in self.header.
   No one expects to find anything much in there.

3) read fills in self.data with a numpy array holding the image.
   Some info are automatically exposed from data:
   * self.shape is the image dimensions,
   * self.dtype is the numpy.dtype of the data.

4) The member variables "_need_a_seek_to_read" and "_need_a_real_file" are there
   in case you have
   trouble with the transparent handling of bz2 and gz files.

5) Add your new module as an import into fabio.fabioformats.
   Your class will be registered automatically.

6) Fill out the magic numbers for your format in fabio.openimage if you know
   them (the characteristic first few bytes in the file)

7) Declare your new file in meson.build

8) Upload a testimage to the file release system and create a unittest testcase
   which opens an example of your new format, confirming the image has actually
   been read in successfully (eg check the mean, max, min and esd are all correct,
   perhaps orientation too)

9) Run pylint on your code and then please go clean it up. Have a go at mine
   while you are at it, before requesting a pull-request on github.

10) Bask in the warm glow of appreciation when someone unexpectedly learns they
   don't need to convert their data into another format

"""

__authors__ = ["author"]
__contact__ = "name@institut.org"
__license__ = "MIT"
__copyright__ = "Institut"
__date__ = "09/02/2023"

import logging
logger = logging.getLogger(__name__)
import numpy
from .fabioimage import FabioImage, OrderedDict


class TemplateImage(FabioImage):
    """FabIO image class for Images for XXX detector

    Put some documentation here
    """

    DESCRIPTION = "Name of the file format"

    DEFAULT_EXTENSIONS = []

    def __init__(self, *arg, **kwargs):
        """
        Generic constructor
        """
        FabioImage.__init__(self, *arg, **kwargs)

    def _readheader(self, infile):
        """
        Read and decode the header of an image:

        :param infile: Opened python file (can be stringIO or bzipped file)
        """
        # list of header key to keep the order (when writing)
        self.header = self.check_header()

    def read(self, fname, frame=None):
        """
        Try to read image

        :param fname: name of the file
        :param frame: number of the frame
        """

        self.resetvals()
        with self._open(fname) as infile:
            self._readheader(infile)
            # read the image data and declare it

        shape = (50, 60)
        self.data = numpy.zeros(shape, dtype=self.uint16)
        # Nota: dim1, dim2, bytecode and bpp are properties defined by the dataset
        return self


# This is for compatibility with old code:
templateimage = TemplateImage
