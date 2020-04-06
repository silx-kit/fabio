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
# Unit tests

# builds on stuff from ImageD11.test.testpeaksearch

Updated by Jerome Kieffer (jerome.kieffer@esrf.eu), 2011

"""

__date__ = "03/04/2020"
__author__ = "jerome Kieffer"

import unittest
import os
import logging

logger = logging.getLogger(__name__)

import fabio
from fabio.dm3image import Dm3Image
from ..utilstest import UtilsTest

# statistics come from fit2d I think
# filename dim1 dim2 min max mean stddev
TESTIMAGES = [("ref_d20x_310mm.dm3", (2048, 2048), -31842.354, 23461.672, 569.38782, 1348.4183),
              ("ref_d20x_310mm.dm3.gz", (2048, 2048), -31842.354, 23461.672, 569.38782, 1348.4183),
              ("ref_d20x_310mm.dm3.bz2", (2048, 2048), -31842.354, 23461.672, 569.38782, 1348.4183)]


class TestDm3Image(unittest.TestCase):
    """
    """

    def setUp(self):
        """ Download images """
        self.im_dir = os.path.dirname(UtilsTest.getimage("ref_d20x_310mm.dm3.bz2"))

    def test_read(self):
        """ check we can read dm3 images"""
        for info in TESTIMAGES:
            name, shape, mini, maxi, mean, stddev = info
            fname = os.path.join(self.im_dir, name)
            obj1 = Dm3Image()
            obj1.read(fname)
            obj2 = fabio.open(fname)
            for obj in (obj1, obj2):
                self.assertAlmostEqual(mini, obj.getmin(), 2, "getmin")
                self.assertAlmostEqual(maxi, obj.getmax(), 2, "getmax")
                got_mean = obj.getmean()
                self.assertAlmostEqual(mean, got_mean, 2, "getmean exp %s != got %s" % (mean, got_mean))
                self.assertAlmostEqual(stddev, obj.getstddev(), 2, "getstddev")
                self.assertEqual(shape, obj.shape)


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestDm3Image))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
