#!/usr/bin/env python
# -*- coding: utf8 -*- 

## Automatically adapted for numpy.oldnumeric Oct 05, 2007 by alter_code1.py



"""
Test cases for the fabioimage class

testsuite by Jerome Kieffer (Jerome.Kieffer@esrf.eu)
"""

import unittest, os, sys
import numpy as N
import numpy.random as RandomArray
import logging


for idx, opts in enumerate(sys.argv[:]):
    if opts in ["-d", "--debug"]:
        logging.basicConfig(level=logging.DEBUG)
        sys.argv.pop(idx)
try:
    logging.debug("tests loaded from file: %s" % __file__)
except:
    __file__ = os.getcwd()

from utilstest import UtilsTest
from fabio.fabioimage import fabioimage

class test50000(unittest.TestCase):
    """ test with 50000 everywhere"""
    def setUp(self):
        """make the image"""
        dat = N.ones((1024, 1024), N.uint16)
        dat = (dat * 50000).astype(N.uint16)
        assert dat.dtype.char == N.ones((1), N.uint16).dtype.char
        hed = {"Title":"50000 everywhere"}
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
        dat2 = N.zeros((1024, 1024), N.uint16)
        hed = {"Title":"zeros and 100"}
        self.cord = [ 256, 256, 790, 768 ]
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


class testopen(unittest.TestCase):
    """check opening compressed files"""

    def setUp(self):
        """ create test files"""
        open("testfile", "wb").write("{ hello }")
        os.system("gzip testfile")
        open("testfile", "wb").write("{ hello }")
        os.system("bzip2 testfile")
        open("testfile", "wb").write("{ hello }")
        self.obj = fabioimage()

    def tearDown(self):
        """clean up"""
        for name in ["testfile", "testfile.gz", "testfile.bz2"]:
            if os.path.exists(name):
                os.remove(name)

    def testFlat(self):
        """ no compression"""
        res = self.obj._open("testfile").read()
        self.assertEqual(res , "{ hello }")

    def testgz(self):
        """ gzipped """
        res = self.obj._open("testfile.gz").read()
        self.assertEqual(res , "{ hello }")

    def testbz2(self):
        """ bzipped"""
        res = self.obj._open("testfile.bz2").read()
        self.assertEqual(res , "{ hello }")


NAMES = { N.uint8 :  "N.uint8",
          N.int8  :  "N.int8" ,
          N.uint16:  "N.uint16",
          N.int16 :  "N.int16" ,
          N.uint32:  "N.uint32" ,
          N.int32 :  "N.int32"   ,
          N.float32: "N.float32" ,
          N.float64: "N.float64"}


class testPILimage(unittest.TestCase):
    """ check PIL creation"""
    def setUp(self):
        """ list of working numeric types"""
        self.okformats = [N.uint8,
                          N.int8,
                          N.uint16,
                          N.int16,
                          N.uint32,
                          N.int32,
                          N.float32]


    def mkdata(self, shape, typ):
        """ generate [01] testdata """
        return (RandomArray.random(shape)).astype(typ)


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
        return (RandomArray.random(shape) * sys.maxint / 10).astype(typ)

class testPILimage3(testPILimage):
    """ check with different numbers"""
    def mkdata(self, shape, typ):
        """ positive, negative and big"""
        return ((RandomArray.random(shape) - 0.5) * sys.maxint / 10).astype(typ)

def test_suite_all_fabio():
    testSuite = unittest.TestSuite()

    testSuite.addTest(test50000("testgetmax"))
    testSuite.addTest(test50000("testgetmin"))
    testSuite.addTest(test50000("testgetmean"))
    testSuite.addTest(test50000("getstddev"))

    testSuite.addTest(testslices("testgetmax"))
    testSuite.addTest(testslices("testgetmin"))
    testSuite.addTest(testslices("testintegratearea"))

    testSuite.addTest(testopen("testFlat"))
    testSuite.addTest(testopen("testgz"))
    testSuite.addTest(testopen("testbz2"))

    testSuite.addTest(testPILimage("testpil"))
    testSuite.addTest(testPILimage2("testpil"))
    testSuite.addTest(testPILimage3("testpil"))

    return testSuite

if __name__ == '__main__':

    mysuite = test_suite_all_fabio()
    runner = unittest.TextTestRunner()
    runner.run(mysuite)
