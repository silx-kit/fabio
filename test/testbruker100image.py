#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Project: Fable Input Output
#             https://github.com/kif/fabio
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
#bruker100 Unit tests

19/01/2015
"""
from __future__ import print_function, with_statement, division, absolute_import
import unittest
import os
import numpy
import gzip
import bz2
if __name__ == '__main__':
    import pkgutil
    __path__ = pkgutil.extend_path([os.path.dirname(__file__)], "fabio.test")
from .utilstest import UtilsTest

logger = UtilsTest.get_logger(__file__)
from fabio.bruker100image import bruker100image
from fabio.openimage import openimage

# filename dim1 dim2 min max mean stddev
TESTIMAGES = """NaCl_10_01_0009.sfrm         512 512 4 4294967286 65570.46 16777087.80
                NaCl_10_01_0009.sfrm.gz      512 512 4 4294967286 65570.46 16777087.80
                NaCl_10_01_0009.sfrm.bz2     512 512 4 4294967286 65570.46 16777087.80"""
REFIMAGE = "NaCl_10_01_0009_set_to_4-bytes.tiff.bz2"


class TestBruker100(unittest.TestCase):
    """ check some read data from bruker version100 detector"""
    def setUp(self):
        """
        download images
        """
        UtilsTest.getimage(REFIMAGE)
        self.im_dir = os.path.dirname(UtilsTest.getimage(TESTIMAGES.split()[0] + ".bz2"))

    def test_read(self):
        """ check we can read bruker100 images"""
        for line in TESTIMAGES.split("\n"):
            vals = line.split()
            name = vals[0]
            dim1, dim2 = [int(x) for x in vals[1:3]]
            mini, maxi, mean, stddev = [float(x) for x in vals[3:]]
            obj = bruker100image()
            obj.read(os.path.join(self.im_dir, name))
            self.assertAlmostEqual(mini, obj.getmin(), 2, "getmin")
            self.assertAlmostEqual(maxi, obj.getmax(), 2, "getmax")
            self.assertAlmostEqual(mean, obj.getmean(), 2, "getmean")
            self.assertAlmostEqual(stddev, obj.getstddev(), 2, "getstddev")
            self.assertEqual(dim1, obj.dim1, "dim1")
            self.assertEqual(dim2, obj.dim2, "dim2")

    def test_same(self):
        """ check we can read bruker100 images"""
        ref = openimage(os.path.join(self.im_dir, REFIMAGE))
        for line in TESTIMAGES.split("\n"):
            obt = openimage(os.path.join(self.im_dir, line.split()[0]))
            self.assert_(abs(ref.data - obt.data).max() == 0, "data are the same")


def suite():
    testsuite = unittest.TestSuite()
    testsuite.addTest(TestBruker100("test_read"))
    testsuite.addTest(TestBruker100("test_same"))
    return testsuite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())

