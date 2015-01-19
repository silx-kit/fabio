#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test cases for the fabioimage class

testsuite by Jerome Kieffer (Jerome.Kieffer@esrf.eu)
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
from fabio.fabioimage import fabioimage
from fabio.third_party import six

class test50000(unittest.TestCase):
    """ test with 50000 everywhere"""
    def setUp(self):
        """make the image"""
        dat = numpy.ones((1024, 1024), numpy.uint16)
        dat = (dat * 50000).astype(numpy.uint16)
        assert dat.dtype.char == numpy.ones((1), numpy.uint16).dtype.char
        hed = {"Title": "50000 everywhere"}
        self.obj = fabioimage(dat, hed)

    def testgetmax(self):
        """check max"""
        self.assertEqual(self.obj.getmax(), 50000)

    def testgetmin(self):
        """check min"""
        self.assertEqual(self.obj.getmin(), 50000)

    def testgetmean(self):
        """check mean"""
        self.assertEqual(self.obj.getmean(), 50000)

    def getstddev(self):
        """check stddev"""
        self.assertEqual(self.obj.getstddev(), 0)


class testslices(unittest.TestCase):
    """check slicing"""
    def setUp(self):
        """make test data"""
        dat2 = numpy.zeros((1024, 1024), numpy.uint16)
        hed = {"Title": "zeros and 100"}
        self.cord = [256, 256, 790, 768]
        self.obj = fabioimage(dat2, hed)
        self.slic = slic = self.obj.make_slice(self.cord)
        # Note - d2 is modified *after* fabioimage is made
        dat2[slic] = dat2[slic] + 100
        assert self.obj.maxval is None
        assert self.obj.minval is None
        self.npix = (slic[0].stop - slic[0].start) * \
            (slic[1].stop - slic[1].start)

    def testgetmax(self):
        """check max"""
        self.assertEqual(self.obj.getmax(), 100)

    def testgetmin(self):
        """check min"""
        self.assertEqual(self.obj.getmin(), 0)

    def testintegratearea(self):
        """ check integrations"""
        self.obj.resetvals()
        area1 = self.obj.integrate_area(self.cord)
        self.obj.resetvals()
        area2 = self.obj.integrate_area(self.slic)
        self.assertEqual(area1, area2)
        self.assertEqual(area1, self.npix * 100)

    def testRebin(self):
        """Test the rebin method"""
        big = numpy.arange(64).reshape((8, 8))
        res = numpy.array([[13, 17], [45, 49]])
        fabimg = fabioimage(data=big, header={})
        fabimg.rebin(4, 4)
        self.assertEqual(abs(res - fabimg.data).max(), 0, "data are the same after rebin")


class testopen(unittest.TestCase):
    """check opening compressed files"""
    testfile = os.path.join(UtilsTest.tempdir, "testfile")

    def setUp(self):
        """ create test files"""
        if not os.path.isfile(self.testfile):
            open(self.testfile, "wb").write(b"{ hello }")
        if not os.path.isfile(self.testfile + ".gz"):
            gzip.open(self.testfile + ".gz", "wb").write(b"{ hello }")
        if not os.path.isfile(self.testfile + ".bz2"):
            bz2.BZ2File(self.testfile + ".bz2", "wb").write(b"{ hello }")
        self.obj = fabioimage()

    def testFlat(self):
        """ no compression"""
        res = self.obj._open(self.testfile).read()
        self.assertEqual(res, b"{ hello }")

    def testgz(self):
        """ gzipped """
        res = self.obj._open(self.testfile + ".gz").read()
        self.assertEqual(res, b"{ hello }")

    def testbz2(self):
        """ bzipped"""
        res = self.obj._open(self.testfile + ".bz2").read()
        self.assertEqual(res, b"{ hello }")


NAMES = {numpy.uint8:   "numpy.uint8",
         numpy.int8:    "numpy.int8" ,
         numpy.uint16:  "numpy.uint16",
         numpy.int16:   "numpy.int16" ,
         numpy.uint32:  "numpy.uint32" ,
         numpy.int32:   "numpy.int32"   ,
         numpy.float32: "numpy.float32" ,
         numpy.float64: "numpy.float64"}


class testPILimage(unittest.TestCase):
    """ check PIL creation"""
    def setUp(self):
        """ list of working numeric types"""
        self.okformats = [numpy.uint8,
                          numpy.int8,
                          numpy.uint16,
                          numpy.int16,
                          numpy.uint32,
                          numpy.int32,
                          numpy.float32]

    def mkdata(self, shape, typ):
        """ generate [01] testdata """
        return (numpy.random.random(shape)).astype(typ)

    def testpil(self):

        for typ in self.okformats:
            name = NAMES[typ]
            for shape in [(10, 20), (431, 1325)]:
                testdata = self.mkdata(shape, typ)
                img = fabioimage(testdata, {"title":"Random data"})
                pim = img.toPIL16()
                for i in [ 0, 5, 6, shape[1] - 1 ]:
                    for j in [0, 5, 7, shape[0] - 1 ]:
                        errstr = name + " %d %d %f %f t=%s" % (
                            i, j, testdata[j, i], pim.getpixel((i, j)), typ)

                        er1 = img.data[j, i] - pim.getpixel((i, j))
                        er2 = img.data[j, i] + pim.getpixel((i, j))

                        # difference as % error in case of rounding
                        if er2 != 0.:
                            err = er1 / er2
                        else:
                            err = er1

                        self.assertAlmostEquals(err,
                                                 0,
                                                 6,
                                                 errstr)


class testPILimage2(testPILimage):
    """ check with different numbers"""
    def mkdata(self, shape, typ):
        """ positive and big"""
        return (numpy.random.random(shape) * sys.maxsize / 10).astype(typ)


class testPILimage3(testPILimage):
    """ check with different numbers"""
    def mkdata(self, shape, typ):
        """ positive, negative and big"""
        return ((numpy.random.random(shape) - 0.5) * sys.maxsize / 10).astype(typ)


def test_suite_all_fabio():
    testSuite = unittest.TestSuite()

    testSuite.addTest(test50000("testgetmax"))
    testSuite.addTest(test50000("testgetmin"))
    testSuite.addTest(test50000("testgetmean"))
    testSuite.addTest(test50000("getstddev"))

    testSuite.addTest(testslices("testgetmax"))
    testSuite.addTest(testslices("testgetmin"))
    testSuite.addTest(testslices("testintegratearea"))
    testSuite.addTest(testslices("testRebin"))

    testSuite.addTest(testopen("testFlat"))
    testSuite.addTest(testopen("testgz"))
    testSuite.addTest(testopen("testbz2"))

    if fabio.fabioimage.Image is not None:
        testSuite.addTest(testPILimage("testpil"))
        testSuite.addTest(testPILimage2("testpil"))
        testSuite.addTest(testPILimage3("testpil"))
    else:
        logger.warning("Skipping PIL related tests")
    return testSuite

if __name__ == '__main__':

    mysuite = test_suite_all_fabio()
    runner = unittest.TextTestRunner()
    runner.run(mysuite)
