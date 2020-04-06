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
# THE SOFTWARE.
#

"""
Read the fit2d ascii image output
        + Jon Wright, ESRF
"""

import numpy
import logging

_logger = logging.getLogger(__name__)

from .fabioimage import FabioImage


class Fit2dSpreadsheetImage(FabioImage):
    """
    Read a fit2d ascii format
    """

    DESCRIPTION = "Fit2d spreadsheet ascii file format"

    DEFAULT_EXTENSIONS = ["spr"]

    def _readheader(self, infile):
        """
        Read the header of the file
        """
        line = infile.readline()
        while line.startswith(b"#"):
            line = infile.readline()
        items = line.split()
        xdim = int(items[0])
        ydim = int(items[1])
        self.header['title'] = line
        self.header['Dim_1'] = xdim
        self.header['Dim_2'] = ydim

    def read(self, fname, frame=None):
        """
        Read in header into self.header and
            the data   into self.data
        """
        self.header = self.check_header()
        self.resetvals()
        infile = self._open(fname)
        self._readheader(infile)
        # Compute image size
        try:
            dim1 = int(self.header['Dim_1'])
            dim2 = int(self.header['Dim_2'])
            self._shape = dim2, dim1
        except (ValueError, KeyError):
            raise IOError("file %s is corrupt, cannot read it" % str(fname))

        self._dtype = numpy.dtype(numpy.float32)

        # now read the data into the array
        try:
            vals = []
            for line in infile.readlines():
                try:
                    vals.append([float(x) for x in line.split()])
                except Exception:
                    pass
            self.data = numpy.array(vals).astype(self._dtype)
            assert self.data.shape == self._shape
            self._shape = None
            self._dtype = None
        except Exception:
            _logger.debug("Backtrace", exc_info=True)
            raise IOError("Error reading ascii")

        self.resetvals()
        return self


fit2dspreadsheetimage = Fit2dSpreadsheetImage
