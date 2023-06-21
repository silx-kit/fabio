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
28/11/2014
"""

import unittest
import os
import logging

from ..utilstest import UtilsTest

logger = logging.getLogger(__name__)

from fabio.GEimage import GEimage


class TestGE(unittest.TestCase):

    # filename dim1 dim2 min max mean stddev
    TESTIMAGES = [
        ("GE_aSI_detector_image_1529.bz2", (2048, 2048), (1515, 16353, 1833.0311, 56.9124)),
        ("GE_aSI_detector_image_1529.gz", (2048, 2048), (1515, 16353, 1833.0311, 56.9124)),
        ("GE_aSI_detector_image_1529", (2048, 2048), (1515, 16353, 1833.0311, 56.9124)),
        ("GE_image_1frame_intact_header.ge", (2048, 2048), (1515, 16353, 2209.1113, 437.6377)),
        ("GE_image_1frame_blanked_header.ge", (2048, 2048), (1300, 16349, 1886.41111, 117.0603)),
    ]

    def setUp(self):
        """
        download images
        """
        for info in self.TESTIMAGES:
            UtilsTest.getimage(info[0])

    def test_read(self):
        for info in self.TESTIMAGES:
            name = info[0]
            with self.subTest(name=name):
                dim1, dim2 = info[1]
                mini, maxi, mean, stddev = info[2]
                shape = dim2, dim1
                obj = GEimage()
                obj.read(os.path.join(UtilsTest.resources.data_home, name))

                self.assertAlmostEqual(mini, obj.getmin(), 4, "getmin")
                self.assertAlmostEqual(maxi, obj.getmax(), 4, "getmax")
                self.assertAlmostEqual(mean, obj.getmean(), 4, "getmean")
                self.assertAlmostEqual(stddev, obj.getstddev(), 4, "getstddev")
                self.assertEqual(shape, obj.shape)


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestGE))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
