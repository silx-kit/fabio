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

Test for MRC file format imagess.

"""

import unittest
import os
import logging

logger = logging.getLogger(__name__)

import fabio
from ...mrcimage import MrcImage
from ...openimage import openimage
from ..utilstest import UtilsTest


class TestMrc(unittest.TestCase):
    """basic test"""
    mrcfilename = ('EMD-3001.map', "0p67_5s_0000.mrc")
    npyfilename = ('EMD-3001.npy', "0p67_5s_0000.npy")
    results = """EMD-3001.map   73 43  -0.36814222  0.678705 0.0062340125 0.16349247
                 0p67_5s_0000.mrc 2048 2048 -344.0 33553.0 82.653259 243.213061"""

    def setUp(self):
        """Download files"""
        self.fn = {}
        for i in self.mrcfilename + self.npyfilename:
            self.fn[i] = UtilsTest.getimage(i + ".bz2")[:-4]
        for i in self.fn:
            assert os.path.exists(self.fn[i])

    def test_read(self):
        """ check we can read mrc images"""
        for results in self.results.split("\n"):
            vals = results.split()
            dim1, dim2 = [int(x) for x in vals[1:3]]
            shape = dim2, dim1
            mini, maxi, mean, stddev = [float(x) for x in vals[3:]]
            for ext in ["", ".gz", ".bz2"]:
                filename = self.fn[vals[0]] + ext
                try:
                    obj = openimage(filename)
                except Exception as err:
                    logger.error("unable to read: %s", filename)
                    raise err
                self.assertAlmostEqual(mini, obj.getmin(), 4, f"{filename} getmin")
                self.assertAlmostEqual(maxi, obj.getmax(), 4, f"{filename} getmax")
                self.assertAlmostEqual(mean, obj.getmean(), 4, f"{filename} getmean")
                self.assertAlmostEqual(stddev, obj.getstddev(), 4, f"{filename} getstddev")
                self.assertEqual(shape, obj.shape, f"{filename} shape")

    def test_same(self):
        """ see if we can read mrc images and if they are the same as the numpy dump"""
        for mrcfilename, npyfilename in zip(self.mrcfilename, self.npyfilename):
            logger.info("Comparing files %s and %s", mrcfilename, npyfilename)
            mrc = MrcImage()
            mrc.read(self.fn[mrcfilename])
            npy = fabio.open(self.fn[npyfilename])
            diff = (mrc.data - npy.data)
            self.assertAlmostEqual(abs(diff).sum(), 0, 4, msg=mrcfilename)


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestMrc))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
