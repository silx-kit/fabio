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
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#


"""
Read the fit2d ascii image output
        + Jon Wright, ESRF
"""
# Get ready for python3:
from __future__ import absolute_import, print_function, with_statement, division
import numpy

from .fabioimage import FabioImage




class Fit2dSpreadsheetImage(FabioImage):
    """
    Read a fit2d ascii format
    """

    def _readheader(self, infile):
        """

        TODO : test for minimal attributes?
        """
        line = infile.readline()
        try:
            items = line.split()
            xdim = int(items[0])
            ydim = int(items[1])
        except:
            raise
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
            self.dim1 = int(self.header['Dim_1'])
            self.dim2 = int(self.header['Dim_2'])
        except:
            raise Exception("file", str(fname) + \
                                "is corrupt, cannot read it")
        bytecode = numpy.float32

        self.bpp = len(numpy.array(0, bytecode).tostring())

        # now read the data into the array
        try:
            vals = []
            for line in infile.readlines():
                try:
                    vals.append([float(x) for x in line.split()])
                except:
                    pass
            self.data = numpy.array(vals).astype(bytecode)
            assert self.data.shape == (self.dim2, self.dim1)

        except:
            raise IOError("Error reading ascii")

        self.resetvals()
        # ensure the PIL image is reset
        self.pilimage = None
        return self

fit2dspreadsheetimage = Fit2dSpreadsheetImage