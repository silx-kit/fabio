#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
# Unit tests

# builds on stuff from ImageD11.test.testpeaksearch
"""

import unittest, os
import logging
import sys
from testopenimage import testOXDUNC

for idx, opts in enumerate(sys.argv[:]):
    if opts in ["-d", "--debug"]:
        logging.basicConfig(level=logging.DEBUG)
        sys.argv.pop(idx)
try:
    logging.debug("tests loaded from file: %s" % __file__)
except:
    __file__ = os.getcwd()

from utilstest import UtilsTest
from fabio.OXDimage import OXDimage
from fabio.openimage import openimage

# filename dim1 dim2 min max mean stddev values are from OD Sapphire 3.0 
TESTIMAGES = """b191_1_9_1_uncompressed.img  512 512 -500 11975 25.70 90.2526
b191_1_9_1_uncompressed.img  512 512 -500 11975 25.70 90.2526"""


class testOXD(unittest.TestCase):
    def setUp(self):
        UtilsTest.getimage("b191_1_9_1.img.bz2")
        UtilsTest.getimage("b191_1_9_1_uncompressed.img.bz2")

    def test_read(self):
        "Test reading of compressed OXD images"
        for line in TESTIMAGES.split("\n"):
            vals = line.split()
            name = vals[0]
            dim1, dim2 = [int(x) for x in vals[1:3]]
            mini, maxi, mean, stddev = [float(x) for x in vals[3:]]
            obj = OXDimage()
            obj.read(os.path.join("testimages", name))

            self.assertAlmostEqual(mini, obj.getmin(), 2, "getmin")
            self.assertAlmostEqual(maxi, obj.getmax(), 2, "getmax")
            self.assertAlmostEqual(mean, obj.getmean(), 2, "getmean")
            self.assertAlmostEqual(stddev, obj.getstddev(), 2, "getstddev")
            self.assertEqual(dim1, obj.dim1, "dim1")
            self.assertEqual(dim2, obj.dim2, "dim2")



class testOXD_same(unittest.TestCase):
    def setUp(self):
        UtilsTest.getimage("b191_1_9_1.img.bz2")
        UtilsTest.getimage("b191_1_9_1_uncompressed.img.bz2")
        self.f1 = os.path.join("testimages", "b191_1_9_1.img")
        self.f2 = os.path.join("testimages", "b191_1_9_1_uncompressed.img")
    def test_same(self):
        """test if images are actually the same"""
        o1 = openimage(self.f1)
        o2 = openimage(self.f2)
        for attr in ["getmin", "getmax", "getmean", "getstddev"]:
            a1 = getattr(o1, attr)()
            a2 = getattr(o2, attr)()
            self.assertEqual(a1, a2, attr)


def test_suite_all_OXD():
    testSuite = unittest.TestSuite()
    testSuite.addTest(testOXD("test_read"))
    testSuite.addTest(testOXD_same("test_same"))
    return testSuite

if __name__ == '__main__':
    mysuite = test_suite_all_OXD()
    runner = unittest.TextTestRunner()
    runner.run(mysuite)

