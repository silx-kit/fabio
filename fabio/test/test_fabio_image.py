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
import unittest
import sys
import os
import numpy
import copy
import logging

logger = logging.getLogger(__name__)

from ..fabioimage import FabioImage
from .. import fabioutils
from ..utils import pilutils
from .utilstest import UtilsTest

try:
    import pathlib
except ImportError:
    try:
        import pathlib2 as pathlib
    except ImportError:
        pathlib = None


class Test50000(unittest.TestCase):
    """ test with 50000 everywhere"""

    def setUp(self):
        """make the image"""
        dat = numpy.ones((1024, 1024), numpy.uint16)
        dat = (dat * 50000).astype(numpy.uint16)
        assert dat.dtype.char == numpy.ones((1), numpy.uint16).dtype.char
        hed = {"Title": "50000 everywhere"}
        self.obj = FabioImage(dat, hed)

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        self.obj = None

    def testgetmax(self):
        """check max"""
        self.assertEqual(self.obj.getmax(), 50000)

    def testgetmin(self):
        """check min"""
        self.assertEqual(self.obj.getmin(), 50000)

    def testgetmean(self):
        """check mean"""
        self.assertEqual(self.obj.getmean(), 50000)

    def testgetstddev(self):
        """check stddev"""
        self.assertEqual(self.obj.getstddev(), 0)

    def testcopy(self):
        "test the copy statement"
        c = copy.copy(self.obj)
        self.assertNotEqual(id(c), id(self.obj), "object differ")
        self.assertEqual(c.header, self.obj.header, "header are the same")
        self.assertEqual(abs(c.data - self.obj.data).max(), 0, "data are the same")
        self.assertEqual(c.filename, self.obj.filename, "filename is the same")


class TestSlices(unittest.TestCase):
    """check slicing"""

    def setUp(self):
        """make test data"""
        dat2 = numpy.zeros((1024, 1024), numpy.uint16)
        hed = {"Title": "zeros and 100"}
        self.cord = [256, 256, 790, 768]
        self.obj = FabioImage(dat2, hed)
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
        fabimg = FabioImage(data=big, header={})
        fabimg.rebin(4, 4)
        self.assertEqual(abs(res - fabimg.data).max(), 0, "data are the same after rebin")


class TestOpen(unittest.TestCase):
    """check opening compressed files"""
    testfile = os.path.join(UtilsTest.tempdir, "testfile")

    def setUp(self):
        """ create test files"""
        if not os.path.isfile(self.testfile):
            with open(self.testfile, "wb") as f:
                f.write(b"{ hello }")
        if not os.path.isfile(self.testfile + ".gz"):
            with fabioutils.GzipFile(self.testfile + ".gz", "wb") as wf:
                wf.write(b"{ hello }")
        if not os.path.isfile(self.testfile + ".bz2"):
            with fabioutils.BZ2File(self.testfile + ".bz2", "wb") as wf:
                wf.write(b"{ hello }")
        self.obj = FabioImage()

    def testFlat(self):
        """ no compression"""
        res = self.obj._open(self.testfile)
        self.assertEqual(res.read(), b"{ hello }")
        res.close()

    def testgz(self):
        """ gzipped """
        res = self.obj._open(self.testfile + ".gz")
        self.assertEqual(res.read(), b"{ hello }")
        res.close()

    def testbz2(self):
        """ bzipped"""
        res = self.obj._open(self.testfile + ".bz2")
        self.assertEqual(res.read(), b"{ hello }")
        res.close()

    def test_badtype(self):
        self.assertRaises(TypeError, self.obj._open, None)

    def test_pathlib(self):
        if pathlib is None:
            self.skipTest("pathlib is not available")
        path = pathlib.PurePath(self.testfile + ".bz2")
        res = self.obj._open(path)
        self.assertIsNotNone(res)
        res.close()


class TestPilImage(unittest.TestCase):
    """ check PIL creation"""

    def setUp(self):
        if pilutils.Image is None:
            self.skipTest("PIL is not available")

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
            for shape in [(10, 20), (431, 1325)]:
                testdata = self.mkdata(shape, typ)
                img = FabioImage(testdata, {"title": "Random data"})
                pim = img.toPIL16()
                for i in [0, 5, 6, shape[1] - 1]:
                    for j in [0, 5, 7, shape[0] - 1]:
                        errstr = str(typ) + " %d %d %f %f t=%s" % (
                            i, j, testdata[j, i], pim.getpixel((i, j)), typ)

                        er1 = img.data[j, i] - pim.getpixel((i, j))
                        er2 = img.data[j, i] + pim.getpixel((i, j))

                        # difference as % error in case of rounding
                        if er2 != 0.:
                            err = er1 / er2
                        else:
                            err = er1

                        self.assertAlmostEqual(err, 0, 6, errstr)


class TestPilImage2(TestPilImage):
    """ check with different numbers"""

    def mkdata(self, shape, typ):
        """ positive and big"""
        return (numpy.random.random(shape) * sys.maxsize / 10).astype(typ)


class TestPilImage3(TestPilImage):
    """ check with different numbers"""

    def mkdata(self, shape, typ):
        """ positive, negative and big"""
        return ((numpy.random.random(shape) - 0.5) * sys.maxsize / 10).astype(typ)


class TestDeprecatedFabioImage(unittest.TestCase):

    def test_patch_dim(self):
        data = numpy.array(numpy.arange(3 * 10)).reshape(3, 10)
        image = FabioImage(data=data)
        # Usecase found in some projects
        image.dim2, image.dim1 = data.shape
        # It should not change anything
        self.assertEqual(image.shape, data.shape)

    def test_cleanup_pilimage_cache(self):
        data = numpy.array(numpy.arange(3 * 10)).reshape(3, 10)
        image = FabioImage(data=data)
        # It was a way to force clean up of the cache
        image.pilimage = None


class TestFabioImage(unittest.TestCase):

    def test_iter_abort_iteration(self):
        data = numpy.zeros((2, 2))
        image = FabioImage(data=data)
        for frame in image:
            self.assertEqual(frame.data[0, 0], 0)


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestFabioImage))
    testsuite.addTest(loadTests(Test50000))
    testsuite.addTest(loadTests(TestSlices))
    testsuite.addTest(loadTests(TestOpen))
    testsuite.addTest(loadTests(TestPilImage))
    testsuite.addTest(loadTests(TestPilImage2))
    testsuite.addTest(loadTests(TestPilImage3))
    testsuite.addTest(loadTests(TestDeprecatedFabioImage))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
