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
Authors: Henning O. Sorensen & Erik Knudsen
         Center for Fundamental Research: Metal Structures in Four Dimensions
         Risoe National Laboratory
         Frederiksborgvej 399
         DK-4000 Roskilde
         email:erik.knudsen@risoe.dk
         
         and Jon Wright, ESRF
"""
# get ready for python3
from __future__ import with_statement, print_function


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
        if type(data) == type("string"):
            raise Exception("fabioimage.__init__ bad argument - " + \
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
        import cf_io
        try:
            infile = open(fname, 'rb')
        except:
            raise Exception("columnfile: file" + str(fname) + "not found.")
        try:
            (self.data, self.clabels) = cf_io.read(infile)
        except:
            raise Exception("columnfile: read error, file " + str(fname) + " possibly corrupt")
        self.dims = self.data.shape
        infile.close()


