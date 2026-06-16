# coding: utf-8
#
#    Project: X-ray image reader
#             https://github.com/silx-kit/fabio
#
#
#    Copyright (C) European Synchrotron Radiation Facility, Grenoble, France
#
#    Principal author:       Jérôme Kieffer (Jerome.Kieffer@ESRF.eu)
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#  .
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#  .
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.
"""
# Unit tests

# builds on stuff from ImageD11.test.testpeaksearch
28/11/2014
"""

import unittest
import os
import logging
import fabio
import shutil
from .utilstest import UtilsTest

logger = logging.getLogger(__name__)


class TestHeaderNotSingleton(unittest.TestCase):
    def setUp(self):
        """
        download images
        """
        self.file1 = UtilsTest.getimage("mb_LP_1_001.img.bz2")[:-4]

    def testheader(self):
        file2 = self.file1.replace("mb_LP_1_001.img", "mb_LP_1_002.img")
        self.assertTrue(os.path.exists(self.file1))
        if not os.path.exists(file2):
            shutil.copy(self.file1, file2)
        image1 = fabio.open(self.file1)
        image2 = fabio.open(file2)

        self.assertEqual(self.abs_norm(image1.filename), self.abs_norm(self.file1))
        self.assertEqual(self.abs_norm(image2.filename), self.abs_norm(file2))
        self.assertNotEqual(image1.filename, image2.filename)

    def abs_norm(self, fn):
        return os.path.normcase(os.path.abspath(fn))

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        self.file1 = None


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestHeaderNotSingleton))
    return testsuite


if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite())
