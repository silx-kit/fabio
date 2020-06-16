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
# Unit tests for raxis images
28/11/2014
"""
__date__ = "03/04/2020"
import unittest
import os
import logging

logger = logging.getLogger(__name__)

import fabio
from fabio.raxisimage import raxisimage
from ..utilstest import UtilsTest

# filename dim1 dim2 min max mean stddev
TESTIMAGES = """mgzn-20hpt.img     2300 1280 16 15040  287.82 570.72
                mgzn-20hpt.img.bz2 2300 1280 16 15040  287.82 570.72
                mgzn-20hpt.img.gz  2300 1280 16 15040  287.82 570.72"""
#                Seek from end is not supported with gzip


class TestRaxisImage(unittest.TestCase):

    def setUp(self):
        """
        download images
        """
        self.mar = UtilsTest.getimage("mgzn-20hpt.img.bz2")[:-4]

    def test_read(self):
        """
        Test the reading of Mar345 images
        """
        for line in TESTIMAGES.split('\n'):
            vals = line.strip().split()
            name = vals[0]
            logger.debug("Testing file %s" % name)
            dim1, dim2 = [int(x) for x in vals[1:3]]
            shape = dim2, dim1
            mini, maxi, mean, stddev = [float(x) for x in vals[3:]]
            obj = raxisimage()
            obj.read(os.path.join(os.path.dirname(self.mar), name))

            self.assertAlmostEqual(mini, obj.getmin(), 2, "getmin [%s,%s]" % (mini, obj.getmin()))
            self.assertAlmostEqual(maxi, obj.getmax(), 2, "getmax [%s,%s]" % (maxi, obj.getmax()))
            self.assertAlmostEqual(mean, obj.getmean(), 2, "getmean [%s,%s]" % (mean, obj.getmean()))
            self.assertAlmostEqual(stddev, obj.getstddev(), 2, "getstddev [%s,%s]" % (stddev, obj.getstddev()))
            self.assertEqual(shape, obj.shape)

    def _test_write(self):
        self.skipTest("Write is not implemented")
        "Test writing with self consistency at the fabio level"
        for line in TESTIMAGES.split("\n"):
            logger.debug("Processing file: %s" % line)
            vals = line.split()
            name = vals[0]
            obj = raxisimage()
            obj.read(os.path.join(os.path.dirname(self.mar), name))
            obj.write(os.path.join(UtilsTest.tempdir, name))
            other = raxisimage()
            other.read(os.path.join(UtilsTest.tempdir, name))
            self.assertEqual(abs(obj.data - other.data).max(), 0, "data are the same")
            for key in obj.header:
                if key == "filename":
                    continue
                self.assertTrue(key in other.header, "Key %s is in header" % key)
                self.assertEqual(obj.header[key], other.header[key], "value are the same for key %s: [%s|%s]" % (key, obj.header[key], other.header[key]))
            os.unlink(os.path.join(UtilsTest.tempdir, name))

    def test_memoryleak(self):
        """
        This test takes a lot of time, so only in debug mode.
        """
        N = 1000
        if logger.getEffectiveLevel() == logging.DEBUG:
            logger.debug("Testing for memory leak")
            for _ in range(N):
                _img = fabio.open(self.mar)


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestRaxisImage))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
