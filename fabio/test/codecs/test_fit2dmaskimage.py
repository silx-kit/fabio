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
""" Test the fit2d mask reader

Updated by Jerome Kieffer (jerome.kieffer@esrf.eu), 2011
28/11/2014
"""

import unittest
import os
import numpy
import logging

logger = logging.getLogger(__name__)

import fabio
from fabio.fit2dmaskimage import fit2dmaskimage
from ..utilstest import UtilsTest


class TestFaceMask(unittest.TestCase):
    """ test the picture of a face """

    def setUp(self):
        """
        download images
        """
        self.filename = UtilsTest.getimage("face.msk.bz2")[:-4]
        self.edffilename = UtilsTest.getimage("face.edf.bz2")[:-4]

    def test_getmatch(self):
        """ test edf and msk are the same """
        i = fit2dmaskimage()
        i.read(self.filename)
        j = fabio.open(self.edffilename)
        self.assertEqual(i.shape, j.shape)
        self.assertEqual(i.data.shape, j.data.shape)
        diff = j.data - i.data
        sumd = abs(diff).sum(dtype=float)
        self.assertEqual(sumd, 0.0)


class TestClickedMask(unittest.TestCase):
    """ A few random clicks to make a test mask """

    def setUp(self):
        """
        download images
        """
        self.filename = UtilsTest.getimage("fit2d_click.msk.bz2")[:-4]
        self.edffilename = UtilsTest.getimage("fit2d_click.edf.bz2")[:-4]

    def test_read(self):
        """ Check it reads a mask OK """
        i = fit2dmaskimage()
        i.read(self.filename)
        self.assertEqual(i.shape, (1024, 1024))
        self.assertEqual(i.bpp, 1)
        self.assertEqual(i.bytecode, numpy.uint8)
        self.assertEqual(i.data.shape, (1024, 1024))

    def test_getmatch(self):
        """ test edf and msk are the same """
        i = fit2dmaskimage()
        j = fabio.open(self.edffilename)
        i.read(self.filename)
        self.assertEqual(i.data.shape, j.data.shape)
        diff = j.data - i.data
        self.assertEqual(i.getmax(), 1)
        self.assertEqual(i.getmin(), 0)
        sumd = abs(diff).sum(dtype=float)
        self.assertEqual(sumd, 0)


class TestMskWrite(unittest.TestCase):
    """
    Write dummy mask files with various compression schemes

    """

    def setUp(self):
        shape = (199, 211)  # those are prime numbers
        self.data = (numpy.random.random(shape) > 0.6)
        self.header = fit2dmaskimage.check_header()

    def atest(self):
        e = fit2dmaskimage(data=self.data, header=self.header)
        e.write(self.filename)
        r = fabio.open(self.filename)
        self.assertEqual(e.shape, r.shape, "shape are the same")
        if r.header != self.header:
            print("Issue with header in TestMskWrite.testFlat")
            for k, v in r.header.items():
                print(k, v, self.header.get(k))
            print(e.header)
            print(r.header)
            print(self.header)

        else:
            self.assertTrue(r.header == self.header, "header are OK")
        self.assertTrue(abs(r.data - self.data).max() == 0, "data are OK")

    def testFlat(self):
        self.filename = os.path.join(UtilsTest.tempdir, "random.msk")
        self.atest()

    def testGzip(self):
        self.filename = os.path.join(UtilsTest.tempdir, "random.msk.gz")
        self.atest()

    def testBzip2(self):
        self.filename = os.path.join(UtilsTest.tempdir, "random.msk.gz")
        self.atest()

    def tearDown(self):
        if os.path.isfile(self.filename):
            os.unlink(self.filename)


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestFaceMask))
    testsuite.addTest(loadTests(TestClickedMask))
    testsuite.addTest(loadTests(TestMskWrite))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
