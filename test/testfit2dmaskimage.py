#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Test the fit2d mask reader

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

try:
    from .utilstest import UtilsTest
except (ValueError, SystemError):
    from utilstest import UtilsTest

logger = UtilsTest.get_logger(__file__)
fabio = sys.modules["fabio"]
from fabio.fit2dmaskimage import fit2dmaskimage


class TestFaceMask(unittest.TestCase):
    """ test the picture of a face """

    def setUp(self):
        """
        download images
        """
        self.filename = UtilsTest.getimage("face.msk.bz2")[:-4]
        self.edffilename = UtilsTest.getimage("face.edf.bz2") [:-4]


    def test_getmatch(self):
        """ test edf and msk are the same """
        i = fit2dmaskimage()
        i.read(self.filename)
        j = fabio.open(self.edffilename)
        # print "edf: dim1",oe.dim1,"dim2",oe.dim2
        self.assertEqual(i.dim1, j.dim1)
        self.assertEqual(i.dim2, j.dim2)
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
        self.assertEqual(i.dim1 , 1024)
        self.assertEqual(i.dim2 , 1024)
        self.assertEqual(i.bpp , 1)
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
        self.assertEqual(sumd , 0)

class TestMskWrite(unittest.TestCase):
    """
    Write dummy mask files with various compression schemes

    """
    def setUp(self):
        shape = (199, 211)  # those are prime numbers
        self.data = (numpy.random.random(shape) > 0.6)
        self.header = {}

    def testFlat(self):
        self.filename = os.path.join(UtilsTest.tempdir, "random.msk")
        e = fit2dmaskimage(data=self.data, header=self.header)
        e.write(self.filename)
        r = fabio.open(self.filename)
        self.assertEqual(e.dim1, r.dim1, "dim1 are the same")
        self.assertEqual(e.dim2, r.dim2, "dim2 are the same")
        self.assert_(r.header == self.header, "header are OK")
        self.assert_(abs(r.data - self.data).max() == 0, "data are OK")

    def testGzip(self):
        self.filename = os.path.join(UtilsTest.tempdir, "random.msk.gz")
        e = fit2dmaskimage(data=self.data, header=self.header)
        e.write(self.filename)
        r = fabio.open(self.filename)
        self.assert_(r.header == self.header, "header are OK")
        self.assertEqual(e.dim1, r.dim1, "dim1 are the same")
        self.assertEqual(e.dim2, r.dim2, "dim2 are the same")
        self.assert_(abs(r.data - self.data).max() == 0, "data are OK")

    def testBzip2(self):
        self.filename = os.path.join(UtilsTest.tempdir, "random.msk.gz")
        e = fit2dmaskimage(data=self.data, header=self.header)
        e.write(self.filename)
        r = fabio.open(self.filename)
        self.assert_(r.header == self.header, "header are OK")
        self.assertEqual(e.dim1, r.dim1, "dim1 are the same")
        self.assertEqual(e.dim2, r.dim2, "dim2 are the same")
        self.assert_(abs(r.data - self.data).max() == 0, "data are OK")

    def tearDown(self):
        if os.path.isfile(self.filename):
            os.unlink(self.filename)


def test_suite_all_fit2d():
    testSuite = unittest.TestSuite()
    testSuite.addTest(TestFaceMask("test_getmatch"))
    testSuite.addTest(TestClickedMask("test_read"))
    testSuite.addTest(TestClickedMask("test_getmatch"))
    testSuite.addTest(TestMskWrite("testFlat"))
    testSuite.addTest(TestMskWrite("testGzip"))
    testSuite.addTest(TestMskWrite("testBzip2"))
    return testSuite

if __name__ == '__main__':
    mysuite = test_suite_all_fit2d()
    runner = unittest.TextTestRunner()
    runner.run(mysuite)



