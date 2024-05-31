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
# Unit tests

# builds on stuff from ImageD11.test.testpeaksearch
28/11/2014
"""

import unittest
import os
import numpy
import logging

logger = logging.getLogger(__name__)

import fabio
from fabio.mar345image import mar345image
from ..utilstest import UtilsTest

# filename dim1 dim2 min max mean stddev
TESTIMAGES = """example.mar2300     2300 2300 0 999999 180.15 4122.67
                example.mar2300.bz2 2300 2300 0 999999 180.15 4122.67
                example.mar2300.gz  2300 2300 0 999999 180.15 4122.67
                Fe3O4_023_101.mar2560 2560 3072 0 258253 83.61749 198.29895739775
                Fe3O4_023_101.mar2560.bz2 2560 3072 0 258253 83.61749 198.29895739775
                Fe3O4_023_101.mar2560.gz 2560 3072 0 258253 83.61749 198.29895739775"""
# Fe3O4_023_101.mar2560 is a pathological file from Mar555


class TestMar345(unittest.TestCase):

    def setUp(self):
        """
        download images
        """
        self.mar345 = UtilsTest.getimage("example.mar2300.bz2")[:-4]
        self.mar555 = UtilsTest.getimage("Fe3O4_023_101.mar2560.bz2")[:-4]

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        self.mar345 = self.mar555 = None

    def test_read(self):
        """
        Test the reading of Mar345 images
        """
        for line in TESTIMAGES.split('\n'):
            vals = line.strip().split()
            name = vals[0]
            dim1, dim2 = [int(x) for x in vals[1:3]]
            shape = dim2, dim1
            mini, maxi, mean, stddev = [float(x) for x in vals[3:]]
            obj = mar345image()
            obj.read(UtilsTest.getimage(name))

            self.assertAlmostEqual(mini, obj.getmin(), 2, "getmin [%s,%s]" % (mini, obj.getmin()))
            self.assertAlmostEqual(maxi, obj.getmax(), 2, "getmax [%s,%s]" % (maxi, obj.getmax()))
            self.assertAlmostEqual(mean, obj.getmean(), 2, "getmean [%s,%s]" % (mean, obj.getmean()))
            self.assertAlmostEqual(stddev, obj.getstddev(), 2, "getstddev [%s,%s]" % (stddev, obj.getstddev()))
            self.assertEqual(shape, obj.shape, "shape")

    def test_write(self):
        "Test writing with self consistency at the fabio level"
        for line in TESTIMAGES.split("\n"):
            logger.debug("Processing file: %s" % line)
            vals = line.split()
            name = vals[0]
            obj = mar345image()
            obj.read(os.path.join(os.path.dirname(self.mar345), name))
            obj.write(os.path.join(UtilsTest.tempdir, name))
            other = mar345image()
            other.read(os.path.join(UtilsTest.tempdir, name))
            if abs(obj.data - other.data).max():
                logger.error("data for %s are not the same %s", line, numpy.where(obj.data - other.data))
            self.assertEqual(abs(obj.data - other.data).max(), 0, "data are the same")
            for key in obj.header:
                if key == "filename":
                    continue
                self.assertTrue(key in other.header, "Key %s is in header" % key)
                self.assertEqual(obj.header[key], other.header[key], "value are the same for key %s: [%s|%s]" % (key, obj.header[key], other.header[key]))

            os.unlink(os.path.join(UtilsTest.tempdir, name))

    def test_byteswap_write(self):
        "Test writing with self consistency at the fabio level"
        for line in TESTIMAGES.split("\n"):
            logger.debug("Processing file: %s" % line)
            vals = line.split()
            name = vals[0]
            obj = mar345image()
            obj.read(os.path.join(os.path.dirname(self.mar345), name))
            obj.swap_needed = not (obj.swap_needed)
            obj.write(os.path.join(UtilsTest.tempdir, name))
            other = mar345image()
            other.read(os.path.join(UtilsTest.tempdir, name))
            self.assertEqual(abs(obj.data - other.data).max(), 0, "data are the same")
            for key in obj.header:
                if key == "filename":
                    continue
                self.assertTrue(key in other.header, "Key %s is in header" % key)
                self.assertEqual(obj.header[key], other.header[key], "value are the same for key %s: [%s|%s]" % (key, obj.header[key], other.header[key]))

            os.unlink(os.path.join(UtilsTest.tempdir, name))

    @unittest.skip("very slow test")
    def test_memoryleak(self):
        """
        This test takes a lot of time, so only in debug mode.
        """
        N = 1000
        if logger.getEffectiveLevel() <= logging.INFO:
            logger.debug("Testing for memory leak")
            for i in range(N):
                _img = fabio.open(self.mar345)
                print("reading #%s/%s" % (i, N))

    def test_aux(self):
        """test auxillary functions
        """
        from fabio.ext import mar345_IO
        shape = 120, 130
        size = shape[0] * shape[1]
        img = numpy.random.randint(0, 32000, size).astype("int16")
        b = mar345_IO.precomp(img, shape[-1])
        c = mar345_IO.postdec(b, shape[-1])
        self.assertEqual(abs(c - img).max(), 0, "pre-compression and post-decompression works")

        a = mar345_IO.calc_nb_bits(numpy.arange(8).astype("int32"), 0, 8)
        self.assertEqual(a, 32, "8*4")

        a = mar345_IO.calc_nb_bits(numpy.arange(10).astype("int32"), 0, 10)
        self.assertEqual(a, 50, "10*5")

        a = mar345_IO.calc_nb_bits(numpy.arange(50).astype("int32"), 0, 50)
        self.assertEqual(a, 350, 50 * 7)

        img.shape = shape
        cmp_ccp4 = mar345_IO.compress_pck(img, use_CCP4=True)
        cmp_fab = mar345_IO.compress_pck(img, use_CCP4=False)
        delta = abs(len(cmp_fab) - len(cmp_ccp4))
        if len(cmp_fab) > len(cmp_ccp4):
            logger.error("len(fabio): %s len(ccp4):%s", len(cmp_fab), len(cmp_ccp4))
        self.assertLessEqual(delta, 10, "Compression by FabIO is similar to CCP4")
        img_c_c = mar345_IO.uncompress_pck(cmp_ccp4, overflowPix=False, use_CCP4=True)
        delta = img_c_c - img
        ok = abs(delta).ravel()
        if ok.max() > 0:
            logger.error("img_c_c: %s %s" % numpy.where(delta))
        self.assertEqual(ok.max(), 0, "Compression CCP4 decompression CCP4")

        img_c_f = mar345_IO.uncompress_pck(cmp_ccp4, overflowPix=False, use_CCP4=False)
        delta = img_c_f - img
        ok = abs(delta).ravel()
        if ok.max() > 0:
            logger.error("img_c_f: %s %s" % numpy.where(delta))
        self.assertEqual(ok.max(), 0, "Compression CCP4 decompression Cython")

        img_f_c = mar345_IO.uncompress_pck(cmp_fab, overflowPix=False, use_CCP4=True)
        delta = img_f_c - img
        ok = abs(delta).ravel()
        if ok.max() > 0:
            logger.error("img_f_c: %s %s" % numpy.where(delta))
        self.assertEqual(ok.max(), 0, "Compression Cython decompression CCP4")

        img_f_f = mar345_IO.uncompress_pck(cmp_fab, overflowPix=False, use_CCP4=False)
        delta = img_f_f - img
        ok = abs(delta).ravel()
        if ok.max() > 0:
            logger.error("img_f_f: %s %s" % numpy.where(delta))
        self.assertEqual(ok.max(), 0, "Compression Cython decompression Cython")


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestMar345))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite)
