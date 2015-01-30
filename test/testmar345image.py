#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# Unit tests

# builds on stuff from ImageD11.test.testpeaksearch
28/11/2014
"""
from __future__ import print_function, with_statement, division, absolute_import
import unittest
import sys
import os
import numpy
import gzip
import logging

try:
    from .utilstest import UtilsTest
except (ValueError, SystemError):
    from utilstest import UtilsTest

logger = UtilsTest.get_logger(__file__)
fabio = sys.modules["fabio"]
from fabio.mar345image import mar345image

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

    def test_read(self):
        """
        Test the reading of Mar345 images
        """
        for line in TESTIMAGES.split('\n'):
            vals = line.strip().split()
            name = vals[0]
            dim1, dim2 = [int(x) for x in vals[1:3]]
            mini, maxi, mean, stddev = [float(x) for x in vals[3:]]
            obj = mar345image()
            obj.read(UtilsTest.getimage(name))

            self.assertAlmostEqual(mini, obj.getmin(), 2, "getmin [%s,%s]" % (mini, obj.getmin()))
            self.assertAlmostEqual(maxi, obj.getmax(), 2, "getmax [%s,%s]" % (maxi, obj.getmax()))
            self.assertAlmostEqual(mean, obj.getmean(), 2, "getmean [%s,%s]" % (mean, obj.getmean()))
            self.assertAlmostEqual(stddev, obj.getstddev(), 2, "getstddev [%s,%s]" % (stddev, obj.getstddev()))
            self.assertEqual(dim1, obj.dim1, "dim1")
            self.assertEqual(dim2, obj.dim2, "dim2")

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
            self.assertEqual(abs(obj.data - other.data).max(), 0, "data are the same")
            for key in obj.header:
                if key == "filename":
                    continue
                self.assertTrue(key in other.header, "Key %s is in header" % key)
                self.assertEqual(obj.header[key], other.header[key], "value are the same for key %s: [%s|%s]" % (key, obj.header[key], other.header[key]))

            os.unlink(os.path.join(UtilsTest.tempdir, name))

    def test_memoryleak(self):
        """
        This test takes a lot of time, so only in debug mode.
        """
        N = 1000
        if logger.getEffectiveLevel() <= logging.INFO:
            logger.debug("Testing for memory leak")
            for i in range(N):
                img = fabio.open(self.mar345)
                print("reading #%s/%s" % (i, N))


def test_suite_all_mar345():
    testSuite = unittest.TestSuite()
    testSuite.addTest(TestMar345("test_read"))
    testSuite.addTest(TestMar345("test_write"))
    testSuite.addTest(TestMar345("test_memoryleak"))

    return testSuite

if __name__ == '__main__':
    mysuite = test_suite_all_mar345()
    runner = unittest.TextTestRunner()
    runner.run(mysuite)
