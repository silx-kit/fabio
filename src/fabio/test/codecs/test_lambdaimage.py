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
# THE SOFTWARE.#

"""Test lambda images
"""

import os
import numpy
import fabio.lambdaimage
from fabio.openimage import openimage 
from ..utilstest import UtilsTest

import unittest
import logging
logger = logging.getLogger(__name__)


class TestLambda(unittest.TestCase):
    # filename dim1 dim2 min max mean stddev
    TESTIMAGES = [
        ("l1_test02_00002_m01.nxs", 1554, 516, 0, 548, 0.00, 0.81024), # WIP
        ("l1_test02_00002_m02.nxs", 1554, 516, 0, 0, 0.0, 0.0), # WIP
        ("l1_test02_00002_m03.nxs", 1554, 516, 0, 45, 0.00 ,0.0534), # WIP
        ("l1_test02_00002_master.nxs", 1555, 1813, 0, 548, 0.00, 0.433),  # WIP
    ]

    def test_read(self):
        """
        Test the reading of lambda images
        """
        for params in self.TESTIMAGES:
            name = params[0]
            logger.debug("Processing: %s" % name)
            dim1, dim2 = params[1:3]
            shape = dim2, dim1
            mini, maxi, mean, stddev = params[3:]
            obj = fabio.lambdaimage.LambdaImage()
            filename =UtilsTest.getimage(name) 
            obj.read(filename)

            self.assertAlmostEqual(mini, obj.getmin(), 2, "getmin [%s,%s]" % (mini, obj.getmin()))
            self.assertAlmostEqual(maxi, obj.getmax(), 2, "getmax [%s,%s]" % (maxi, obj.getmax()))
            self.assertAlmostEqual(mean, obj.getmean(), 2, "getmean [%s,%s]" % (mean, obj.getmean()))
            self.assertAlmostEqual(stddev, obj.getstddev(), 2, "getstddev [%s,%s]" % (stddev, obj.getstddev()))

            self.assertEqual(shape, obj.shape, "dim1")
                     
    def test_write(self):
        """read file using fabio.open and save and reopen ... check consistency"""
        for params in self.TESTIMAGES:
            fname = UtilsTest.getimage(params[0])
            obj = openimage(fname)
            self.assertEqual(obj.shape, params[2:0:-1])
 
            dst = os.path.join(UtilsTest.tempdir, os.path.basename(fname))
            obj.write(dst)
            for idx, read_back in enumerate(openimage(dst)):
                self.assertTrue(numpy.all(read_back.data == obj.getframe(idx).data), f"data are the same {fname} #{idx}")  

        
def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestLambda))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
