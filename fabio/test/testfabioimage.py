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
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
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

if __name__ == '__main__':
    import pkgutil
    __path__ = pkgutil.extend_path([os.path.dirname(__file__)], "fabio.test")
from .utilstest import UtilsTest


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

                        self.assertAlmostEquals(err, 0, 6, errstr)


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


def suite():
    testsuite = unittest.TestSuite()

    testsuite.addTest(test50000("testgetmax"))
    testsuite.addTest(test50000("testgetmin"))
    testsuite.addTest(test50000("testgetmean"))
    testsuite.addTest(test50000("getstddev"))

    testsuite.addTest(testslices("testgetmax"))
    testsuite.addTest(testslices("testgetmin"))
    testsuite.addTest(testslices("testintegratearea"))
    testsuite.addTest(testslices("testRebin"))

    testsuite.addTest(testopen("testFlat"))
    testsuite.addTest(testopen("testgz"))
    testsuite.addTest(testopen("testbz2"))

    if fabio.fabioimage.Image is not None:
        testsuite.addTest(testPILimage("testpil"))
        testsuite.addTest(testPILimage2("testpil"))
        testsuite.addTest(testPILimage3("testpil"))
    else:
        logger.warning("Skipping PIL related tests")
    return testsuite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
