#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

Test for PNM images.

Jerome Kieffer, 04/12/2014
"""
import os
import sys
import unittest
try:
    from .utilstest import UtilsTest
except (ValueError, SystemError):
    from utilstest import UtilsTest
logger = UtilsTest.get_logger(__file__)
fabio = sys.modules["fabio"]
from fabio.pnmimage import pnmimage
from fabio.openimage import openimage


class TestPNM(unittest.TestCase):
    """basic test"""
    results = """image0001.pgm  1024 1024  0  28416 353.795654296875   2218.0290682517543"""

    def setUp(self):
        """Download files"""
        self.fn = {}
        for j in self.results.split("\n"):
            i = j.split()[0]
            self.fn[i] = UtilsTest.getimage(i + ".bz2")[:-4]
        for i in self.fn:
            assert os.path.exists(self.fn[i])

    def test_read(self):
        """ check we can read pnm images"""
        vals = self.results.split()
        name = vals[0]
        dim1, dim2 = [int(x) for x in vals[1:3]]
        mini, maxi, mean, stddev = [float(x) for x in vals[3:]]
        obj = openimage(self.fn[name])
        self.assertAlmostEqual(mini, obj.getmin(), 4, "getmin")
        self.assertAlmostEqual(maxi, obj.getmax(), 4, "getmax")
        self.assertAlmostEqual(mean, obj.getmean(), 4, "getmean")
        self.assertAlmostEqual(stddev, obj.getstddev(), 4, "getstddev")
        self.assertEqual(dim1, obj.dim1, "dim1")
        self.assertEqual(dim2, obj.dim2, "dim2")


def test_suite_all_pnm():
    testSuite = unittest.TestSuite()
    testSuite.addTest(TestPNM("test_read"))
    return testSuite

if __name__ == '__main__':
    mysuite = test_suite_all_pnm()
    runner = unittest.TextTestRunner()
    runner.run(mysuite)
