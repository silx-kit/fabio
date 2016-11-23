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
28/11/2014
"""
from __future__ import print_function, with_statement, division, absolute_import
import unittest
import sys
import os
import numpy
import gzip
import bz2

if __name__ == '__main__':
    import pkgutil
    __path__ = pkgutil.extend_path([os.path.dirname(__file__)], "fabio.test")
from .utilstest import UtilsTest


logger = UtilsTest.get_logger(__file__)
fabio = sys.modules["fabio"]
from fabio.GEimage import GEimage
# filename dim1 dim2 min max mean stddev
TESTIMAGES = """GE_aSI_detector_image_1529      2048 2048 1515 16353 1833.0311 56.9124
                GE_aSI_detector_image_1529.gz   2048 2048 1515 16353 1833.0311 56.9124
                GE_aSI_detector_image_1529.bz2  2048 2048 1515 16353 1833.0311 56.9124"""


class TestGE(unittest.TestCase):

    def setUp(self):
        """
        download images
        """
        self.GE = UtilsTest.getimage("GE_aSI_detector_image_1529.bz2")

    def test_read(self):
        for line in TESTIMAGES.split("\n"):
            vals = line.split()
            name = vals[0]
            dim1, dim2 = [int(x) for x in vals[1:3]]
            mini, maxi, mean, stddev = [float(x) for x in vals[3:]]
            obj = GEimage()
            obj.read(os.path.join(os.path.dirname(self.GE), name))

            self.assertAlmostEqual(mini, obj.getmin(), 4, "getmin")
            self.assertAlmostEqual(maxi, obj.getmax(), 4, "getmax")
            self.assertAlmostEqual(mean, obj.getmean(), 4, "getmean")
            self.assertAlmostEqual(stddev, obj.getstddev(), 4, "getstddev")
            self.assertEqual(dim1, obj.dim1, "dim1")
            self.assertEqual(dim2, obj.dim2, "dim2")


def suite():
    testsuite = unittest.TestSuite()
    testsuite.addTest(TestGE("test_read"))
    return testsuite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
