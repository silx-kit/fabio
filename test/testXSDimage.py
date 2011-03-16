#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
# Unit tests

# builds on stuff from ImageD11.test.testpeaksearch
"""

import unittest, os
import logging
import sys
force_build = False
for idx, opts in enumerate(sys.argv[:]):
    if opts in ["-d", "--debug"]:
        logging.basicConfig(level=logging.DEBUG)
        sys.argv.pop(idx)
    if opts in ["-f", "--force"]:
        force_build = True
        sys.argv.pop(sys.argv.index(opts))

try:
    logging.debug("tests loaded from file: %s" % __file__)
except:
    __file__ = os.getcwd()

import numpy as np
from utilstest import UtilsTest
if force_build:
    UtilsTest.forceBuild()
from fabio.xsdimage import xsdimage
from fabio.openimage import openimage

# filename dim1 dim2 min max mean stddev values are from OD Sapphire 3.0 
TESTIMAGES = """XSDataImage.xml  512 512 86 61204 511.63 667.11
XSDataImageInv.xml  512 512  -0.2814 0.22705039 2.81e-08 0.010"""


class testXSD(unittest.TestCase):
    def setUp(self):
        UtilsTest.getimage("XSDataImage.edf")
        UtilsTest.getimage("XSDataImage.xml")
        UtilsTest.getimage("XSDataImageInv.xml")

    def test_read(self):
        "Test reading of XSD images"
        for line in TESTIMAGES.split("\n"):
            vals = line.split()
            name = vals[0]
            dim1, dim2 = [int(x) for x in vals[1:3]]
            mini, maxi, mean, stddev = [float(x) for x in vals[3:]]
            obj = xsdimage()
            obj.read(os.path.join("testimages", name))

            self.assertAlmostEqual(mini, obj.getmin(), 2, "getmin")
            self.assertAlmostEqual(maxi, obj.getmax(), 2, "getmax")
            self.assertAlmostEqual(mean, obj.getmean(), 2, "getmean")
#            print stddev, obj.getstddev()
            self.assertAlmostEqual(stddev, obj.getstddev(), 2, "getstddev")
            self.assertEqual(dim1, obj.dim1, "dim1")
            self.assertEqual(dim2, obj.dim2, "dim2")

    def test_same(self):
        """ test if an image is the same as the EDF equivalent"""
        xsd = openimage(os.path.join("testimages", "XSDataImage.edf"))
        edf = openimage(os.path.join("testimages", "XSDataImage.xml"))
        self.assertAlmostEqual(0, abs(xsd.data - edf.data).max(), 1, "images are the same")

    def test_invert(self):
        """ Tests that 2 matrixes are invert """
        m1 = openimage(os.path.join("testimages", "XSDataImage.xml"))
        m2 = openimage(os.path.join("testimages", "XSDataImageInv.xml"))
        self.assertAlmostEqual(
        abs((np.matrix(m1.data) * np.matrix(m2.data)) - np.identity(m1.data.shape[0])).max(),
        0, 3, "matrices are invert of each other")


def test_suite_all_XSD():
    testSuite = unittest.TestSuite()
    if xsdimage is None:
        logging.warning("xsdimage is None ... probably an import error related to lxml. Skipping test")
    else:
        testSuite.addTest(testXSD("test_read"))
        testSuite.addTest(testXSD("test_same"))
        testSuite.addTest(testXSD("test_invert"))
    return testSuite


if __name__ == '__main__':
    mysuite = test_suite_all_XSD()
    runner = unittest.TextTestRunner()
    runner.run(mysuite)

