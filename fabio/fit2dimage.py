# coding: utf-8
#
#    Project: X-ray image reader
#             https://github.com/kif/fabio
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


"""FabIO reader for Fit2D binary images
"""
# Get ready for python3:
from __future__ import with_statement, print_function, division

__authors__ = ["author"]
__contact__ = "name@institut.org"
__license__ = "GPLv3+"
__copyright__ = "Institut"
__date__ = "21/06/2016"

import logging
logger = logging.getLogger("templateimage")
import numpy
from .fabioimage import FabioImage


class TemplateImage(FabioImage):
    """
    FabIO image class for Images for XXX detector
    """
    def __init__(self, *arg, **kwargs):
        """
        Generic constructor
        """
        FabioImage.__init__(self, *arg, **kwargs)

    def _readheader(self, infile):
        """
        Read and decode the header of an image:
        
        @param infile: Opened python file (can be stringIO or bipped file)  
        """
        # list of header key to keep the order (when writing)
        self.header = self.check_header()

    def read(self, fname, frame=None):
        """
        try to read image 
        @param fname: name of the file
        @param frame: 
        """

        self.resetvals()
        infile = self._open(fname)
        self._readheader(infile)

        # read the image data
        # self.data = numpy.zeros((self.dim2, self.dim1), dtype=self.bytecode)
        # Nota: dim1, dim2, bytecode and bpp are properties defined by the dataset
        return self

# this is not compatibility with old code:
templateimage = TemplateImage
