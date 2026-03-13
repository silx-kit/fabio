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

builds on stuff from ImageD11.test.testpeaksearch
Jerome Kieffer 04/12/2014
"""

import unittest
import logging
from fabio.openimage import openimage
from fabio.edfimage import EdfImage
from fabio.marccdimage import MarccdImage
from fabio.fit2dmaskimage import Fit2dMaskImage
from fabio.OXDimage import OXDimage
from fabio.brukerimage import BrukerImage
from fabio.dtrekimage import DtrekImage
from .utilstest import UtilsTest

logger = logging.getLogger(__name__)


class TestOpenEdf(unittest.TestCase):
    """openimage opening edf"""

    def checkFile(self, filename):
        """check we can read EDF image with openimage"""
        obj = openimage(filename)
        obj2 = EdfImage()
        obj2.read(filename)
        self.assertEqual(obj.data[10, 10], obj2.data[10, 10])
        self.assertEqual(type(obj), type(obj2))
        self.assertEqual(abs(obj.data.astype(int) - obj2.data.astype(int)).sum(), 0)

    def testEdf(self):
        fname = "F2K_Seb_Lyso0675.edf.bz2"
        filename = UtilsTest.getimage(fname)[:-4]
        self.checkFile(filename)

    def testEdfGz(self):
        fname = "F2K_Seb_Lyso0675.edf.gz"
        filename = UtilsTest.getimage(fname)
        self.checkFile(filename)

    def testEdfBz2(self):
        fname = "F2K_Seb_Lyso0675.edf.bz2"
        filename = UtilsTest.getimage(fname)
        self.checkFile(filename)


class TestOpenMccd(unittest.TestCase):
    """openimage opening mccd"""

    def checkFile(self, filename):
        """check we can read it"""
        obj = openimage(filename)
        obj2 = MarccdImage()
        obj2.read(filename)
        self.assertEqual(obj.data[10, 10], obj2.data[10, 10])
        self.assertEqual(type(obj), type(obj2))
        self.assertEqual(abs(obj.data.astype(int) - obj2.data.astype(int)).sum(), 0)

    def testMccd(self):
        fname = "somedata_0001.mccd.bz2"
        filename = UtilsTest.getimage(fname)[:-4]
        self.checkFile(filename)

    def testMccdGz(self):
        fname = "somedata_0001.mccd.gz"
        filename = UtilsTest.getimage(fname)
        self.checkFile(filename)

    def testMccdBz2(self):
        fname = "somedata_0001.mccd.bz2"
        filename = UtilsTest.getimage(fname)
        self.checkFile(filename)


class TestOpenMask(unittest.TestCase):
    """openimage opening fit2d msk"""

    def checkFile(self, filename):
        """check we can read Fit2D mask with openimage"""
        obj = openimage(filename)
        obj2 = Fit2dMaskImage()
        obj2.read(filename)
        self.assertEqual(obj.data[10, 10], obj2.data[10, 10])
        self.assertEqual(type(obj), type(obj2))
        self.assertEqual(abs(obj.data.astype(int) - obj2.data.astype(int)).sum(), 0)
        self.assertEqual(abs(obj.data.astype(int) - obj2.data.astype(int)).sum(), 0)

    def testMask(self):
        """openimage opening fit2d msk"""
        fname = "face.msk.bz2"
        filename = UtilsTest.getimage(fname)[:-4]
        self.checkFile(filename)

    def testMaskGz(self):
        """openimage opening fit2d msk gzip"""
        fname = "face.msk.gz"
        filename = UtilsTest.getimage(fname)
        self.checkFile(filename)

    def testMaskBz2(self):
        """openimage opening fit2d msk bzip"""
        fname = "face.msk.bz2"
        filename = UtilsTest.getimage(fname)
        self.checkFile(filename)


class TestOpenBruker(unittest.TestCase):
    """openimage opening bruker"""

    def checkFile(self, filename):
        """check we can read it"""
        obj = openimage(filename)
        obj2 = BrukerImage()
        obj2.read(filename)
        self.assertEqual(obj.data[10, 10], obj2.data[10, 10])
        self.assertEqual(type(obj), type(obj2))
        self.assertEqual(abs(obj.data.astype(int) - obj2.data.astype(int)).sum(), 0)

    def testBruker(self):
        """openimage opening bruker"""
        fname = "Cr8F8140k103.0026.bz2"
        filename = UtilsTest.getimage(fname)[:-4]
        self.checkFile(filename)

    def testBrukerGz(self):
        """openimage opening bruker gzip"""
        fname = "Cr8F8140k103.0026.gz"
        filename = UtilsTest.getimage(fname)
        self.checkFile(filename)

    def testBrukerBz2(self):
        """openimage opening bruker bzip"""
        fname = "Cr8F8140k103.0026.bz2"
        filename = UtilsTest.getimage(fname)
        self.checkFile(filename)


class TestOpenDtrek(unittest.TestCase):
    """openimage opening adsc"""

    def checkFile(self, filename):
        """check we can read it"""
        obj = openimage(filename)
        obj2 = DtrekImage()
        obj2.read(filename)
        self.assertEqual(obj.data[10, 10], obj2.data[10, 10])
        self.assertEqual(type(obj), type(obj2))
        self.assertEqual(abs(obj.data.astype(int) - obj2.data.astype(int)).sum(), 0)

    def testAdsc(self):
        """openimage opening adsc"""
        fname = "mb_LP_1_001.img.bz2"
        filename = UtilsTest.getimage(fname)[:-4]
        self.checkFile(filename)

    def testAdscGz(self):
        """openimage opening adsc gzip"""
        fname = "mb_LP_1_001.img.gz"
        filename = UtilsTest.getimage(fname)
        self.checkFile(filename)

    def testAdscBz2(self):
        """openimage opening adsc bzip"""
        fname = "mb_LP_1_001.img.bz2"
        filename = UtilsTest.getimage(fname)
        self.checkFile(filename)


class TestOpenOxd(unittest.TestCase):
    """openimage opening adsc"""

    def checkFile(self, filename):
        """check we can read OXD images with openimage"""
        obj = openimage(filename)
        obj2 = OXDimage()
        obj2.read(filename)
        self.assertEqual(obj.data[10, 10], obj2.data[10, 10])
        self.assertEqual(type(obj), type(obj2))
        self.assertEqual(abs(obj.data.astype(int) - obj2.data.astype(int)).sum(), 0)

    def testOxd(self):
        """openimage opening adsc"""
        fname = "b191_1_9_1.img.bz2"
        filename = UtilsTest.getimage(fname)[:-4]
        self.checkFile(filename)

    def testOxdUnc(self):
        """openimage opening adsc"""
        fname = "b191_1_9_1_uncompressed.img.bz2"
        filename = UtilsTest.getimage(fname)[:-4]
        self.checkFile(filename)


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestOpenDtrek))
    testsuite.addTest(loadTests(TestOpenBruker))
    testsuite.addTest(loadTests(TestOpenEdf))
    testsuite.addTest(loadTests(TestOpenMask))
    testsuite.addTest(loadTests(TestOpenMccd))
    testsuite.addTest(loadTests(TestOpenOxd))
    return testsuite


if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite())
