#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Project: Fable Input Output
#             https://github.com/silx-kit/fabio
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
# Unit tests

# builds on stuff from ImageD11.test.testpeaksearch
"""

from __future__ import print_function, with_statement, division, absolute_import
import unittest
import sys
import os
if __name__ == '__main__':
    import pkgutil
    __path__ = pkgutil.extend_path([os.path.dirname(__file__)], "fabio.test")
from .utilstest import UtilsTest

logger = UtilsTest.get_logger(__file__)
fabio = sys.modules["fabio"]

from fabio.xsdimage import xsdimage
import numpy
# filename dim1 dim2 min max mean stddev values are from OD Sapphire 3.0
TESTIMAGES = """XSDataImage.xml     512 512        86 61204     511.63    667.15
                XSDataImageInv.xml  512 512  -0.2814 0.22705039 2.81e-08  0.010"""


class testXSD(unittest.TestCase):
    def setUp(self):
        self.fn = {}
        for i in ["XSDataImage.edf", "XSDataImage.xml", "XSDataImageInv.xml"]:
            self.fn[i] = UtilsTest.getimage(i + ".bz2")[:-4]

    def test_read(self):
        "Test reading of XSD images"
        for line in TESTIMAGES.split("\n"):
            vals = line.split()
            name = vals[0]
            dim1, dim2 = [int(x) for x in vals[1:3]]
            mini, maxi, mean, stddev = [float(x) for x in vals[3:]]
            obj = xsdimage()
            obj.read(self.fn[name])

            self.assertAlmostEqual(mini, obj.getmin(), 2, "getmin")
            self.assertAlmostEqual(maxi, obj.getmax(), 2, "getmax")
            self.assertAlmostEqual(mean, obj.getmean(), 2, "getmean")
            logger.info("%s %s %s" % (name, stddev, obj.getstddev()))
            self.assertAlmostEqual(stddev, obj.getstddev(), 2, "getstddev")
            self.assertEqual(dim1, obj.dim1, "dim1")
            self.assertEqual(dim2, obj.dim2, "dim2")

    def test_same(self):
        """ test if an image is the same as the EDF equivalent"""
        xsd = fabio.open(self.fn["XSDataImage.xml"])
        edf = fabio.open(self.fn["XSDataImage.edf"])
        self.assertAlmostEqual(0, abs(xsd.data - edf.data).max(), 1, "images are the same")

    def test_invert(self):
        """ Tests that 2 matrixes are invert """
        m1 = fabio.open(self.fn["XSDataImage.xml"])
        m2 = fabio.open(self.fn["XSDataImageInv.xml"])
        delta = abs((numpy.matrix(m1.data) * numpy.matrix(m2.data)) - numpy.identity(m1.data.shape[0])).max()
        if delta >= 1e-3:
            logger.error("Matrices are not invert of each other !!! prod = %s", numpy.matrix(m1.data) * numpy.matrix(m2.data))
        self.assert_(delta < 1e-3, "matrices are invert of each other")


def suite():
    testsuite = unittest.TestSuite()
    if xsdimage is None:
        logger.warning("xsdimage is None ... probably an import error related to lxml. Skipping test")
    else:
        testsuite.addTest(testXSD("test_read"))
        testsuite.addTest(testXSD("test_same"))
        testsuite.addTest(testXSD("test_invert"))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())

