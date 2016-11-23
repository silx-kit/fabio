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

Updated by Jerome Kieffer (jerome.kieffer@esrf.eu), 2011
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
from fabio.adscimage import adscimage
from fabio.edfimage import edfimage


# statistics come from fit2d I think
# filename dim1 dim2 min max mean stddev
TESTIMAGES = """mb_LP_1_001.img 3072 3072 0.0000 65535. 120.33 147.38 
                mb_LP_1_001.img.gz  3072 3072 0.0000 65535.  120.33 147.38 
                mb_LP_1_001.img.bz2 3072 3072 0.0000 65535.  120.33 147.38 """


class TestMatch(unittest.TestCase):
    """ 
    check the ??fit2d?? conversion to edf gives same numbers 
    """
    def setUp(self):
        """ Download images """
        self.fn_adsc = UtilsTest.getimage("mb_LP_1_001.img.bz2")[:-4]
        self.fn_edf = UtilsTest.getimage("mb_LP_1_001.edf.bz2")[:-4]

    def testsame(self):
        """test ADSC image match to EDF"""
        im1 = edfimage()
        im1.read(self.fn_edf)
        im2 = adscimage()
        im2.read(self.fn_adsc)
        diff = (im1.data.astype("float32") - im2.data.astype("float32"))
        logger.debug("type: %s %s shape %s %s " % (im1.data.dtype, im2.data.dtype, im1.data.shape, im2.data.shape))
        logger.debug("im1 min %s %s max %s %s " % (im1.data.min(), im2.data.min(), im1.data.max(), im2.data.max()))
        logger.debug("delta min %s max %s mean %s" % (diff.min(), diff.max(), diff.mean()))
        self.assertEqual(abs(diff).max(), 0.0, "asdc data == edf data")


class TestFlatMccdsAdsc(unittest.TestCase):
    """
    """
    def setUp(self):
        """ Download images """
        self.im_dir = os.path.dirname(UtilsTest.getimage("mb_LP_1_001.img.bz2"))

    def test_read(self):
        """ check we can read flat ADSC images"""
        for line in TESTIMAGES.split("\n"):
            vals = line.split()
            name = vals[0]
            dim1, dim2 = [int(x) for x in vals[1:3]]
            mini, maxi, mean, stddev = [float(x) for x in vals[3:]]
            obj = adscimage()
            obj.read(os.path.join(self.im_dir, name))
            self.assertAlmostEqual(mini, obj.getmin(), 2, "getmin")
            self.assertAlmostEqual(maxi, obj.getmax(), 2, "getmax")
            got_mean = obj.getmean()
            self.assertAlmostEqual(mean, got_mean, 2, "getmean exp %s != got %s" % (mean, got_mean))
            self.assertAlmostEqual(stddev, obj.getstddev(), 2, "getstddev")
            self.assertEqual(dim1, obj.dim1, "dim1")
            self.assertEqual(dim2, obj.dim2, "dim2")


def suite():
    testsuite = unittest.TestSuite()
    testsuite.addTest(TestMatch("testsame"))
    testsuite.addTest(TestFlatMccdsAdsc("test_read"))
    return testsuite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())




