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

Test for Nonius Kappa CCD cameras.

"""

import unittest
import os
import logging

logger = logging.getLogger(__name__)

import fabio
from ...kcdimage import kcdimage
from ...openimage import openimage
from ..utilstest import UtilsTest


class TestKcd(unittest.TestCase):
    """basic test"""
    kcdfilename = 'i01f0001.kcd'
    edffilename = 'i01f0001.edf'
    results = """i01f0001.kcd   625 576  96  66814.0 195.3862972   243.58150990245315"""

    def setUp(self):
        """Download files"""
        self.fn = {}
        for i in ["i01f0001.kcd", "i01f0001.edf"]:
            self.fn[i] = UtilsTest.getimage(i + ".bz2")[:-4]
        for i in self.fn:
            assert os.path.exists(self.fn[i])

    def test_read(self):
        """ check we can read kcd images"""
        vals = self.results.split()
        dim1, dim2 = [int(x) for x in vals[1:3]]
        shape = dim2, dim1
        mini, maxi, mean, stddev = [float(x) for x in vals[3:]]
        for ext in ["", ".gz", ".bz2"]:
            try:
                obj = openimage(self.fn[self.kcdfilename] + ext)
            except Exception as err:
                logger.error("unable to read: %s", self.fn[self.kcdfilename] + ext)
                raise err
            self.assertAlmostEqual(mini, obj.getmin(), 4, "getmin" + ext)
            self.assertAlmostEqual(maxi, obj.getmax(), 4, "getmax" + ext)
            self.assertAlmostEqual(mean, obj.getmean(), 4, "getmean" + ext)
            self.assertAlmostEqual(stddev, obj.getstddev(), 4, "getstddev" + ext)
            self.assertEqual(shape, obj.shape, "shape" + ext)

    def test_same(self):
        """ see if we can read kcd images and if they are the same as the EDF """
        kcd = kcdimage()
        kcd.read(self.fn[self.kcdfilename])
        edf = fabio.open(self.fn[self.edffilename])
        diff = (kcd.data.astype("int32") - edf.data.astype("int32"))
        self.assertAlmostEqual(abs(diff).sum(dtype=int), 0, 4)


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestKcd))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
