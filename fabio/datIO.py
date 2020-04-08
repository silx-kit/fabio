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

"""
Authors: Henning O. Sorensen & Erik Knudsen
         Center for Fundamental Research: Metal Structures in Four Dimensions
         Risoe National Laboratory
         Frederiksborgvej 399
         DK-4000 Roskilde
         email:erik.knudsen@risoe.dk

         and Jon Wright, ESRF
"""

import logging

logger = logging.getLogger(__name__)


class fabiodata(object):
    """
    A common class for dataIO in fable
    Contains a 2d numpy array for keeping data, and two lists (clabels and rlabels)
    containing labels for columns and rows respectively
    """

    def __init__(self, data=None, clabels=None, rlabels=None, fname=None):
        """
        set up initial values
        """
        if isinstance(data, str):
            raise RuntimeError("fabioimage.__init__ bad argument - " +
                               "data should be numpy array")
        self.data = data
        if (self.data):
            self.dims = self.data.shape
        self.clabels = clabels
        self.rlabels = rlabels
        if (fname):
            self.read(fname)

    def read(self, fname=None, frame=None):
        """
        To be overridden by format specific subclasses
        """
        raise Exception("Class has not implemented read method yet")

# import stuff from Jon's columnfile things


class columnfile(fabiodata):
    "Concrete fabiodata class"

    def read(self, fname, frame=None):
        from .ext import cf_io
        try:
            infile = open(fname, 'rb')
        except Exception:
            logger.debug("Backtrace", exc_info=True)
            raise Exception("columnfile: file" + str(fname) + "not found.")
        try:
            (self.data, self.clabels) = cf_io.read(infile)
        except Exception:
            logger.debug("Backtrace", exc_info=True)
            raise Exception("columnfile: read error, file " + str(fname) + " possibly corrupt")
        self.dims = self.data.shape
        infile.close()
