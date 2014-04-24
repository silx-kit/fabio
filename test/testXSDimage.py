#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# Unit tests

# builds on stuff from ImageD11.test.testpeaksearch
"""

import unittest
import os
import logging
import sys
logger = logging.getLogger("testXSDimage")
force_build = False

for opts in sys.argv[:]:
    if opts in ["-d", "--debug"]:
        logging.basicConfig(level=logging.DEBUG)
        sys.argv.pop(sys.argv.index(opts))
    elif opts in ["-i", "--info"]:
        logging.basicConfig(level=logging.INFO)
        sys.argv.pop(sys.argv.index(opts))
    elif opts in ["-f", "--force"]:
        force_build = True
        sys.argv.pop(sys.argv.index(opts))
try:
    logger.debug("Tests loaded from file: %s" % __file__)
except:
    __file__ = os.getcwd()

from utilstest import UtilsTest
if force_build:
    UtilsTest.forceBuild()
import fabio
from fabio.xsdimage import xsdimage
import numpy
# filename dim1 dim2 min max mean stddev values are from OD Sapphire 3.0 
TESTIMAGES = """XSDataImage.xml     512 512        86 61204     511.63    667.15
                XSDataImageInv.xml  512 512  -0.2814 0.22705039 2.81e-08  0.010"""


class testXSD(unittest.TestCase):
    def setUp(self):
        self.fn = {}
        for i in ["XSDataImage.edf", "XSDataImage.xml", "XSDataImageInv.xml"]:
            self.fn[i] = UtilsTest.getimage(i + ".bz2")[:-4]

    def test_read(self):
        "Test reading of XSD images"
        for line in TESTIMAGES.split("\n"):
            vals = line.split()
            name = vals[0]
            dim1, dim2 = [int(x) for x in vals[1:3]]
            mini, maxi, mean, stddev = [float(x) for x in vals[3:]]
            obj = xsdimage()
            obj.read(self.fn[name])

            self.assertAlmostEqual(mini, obj.getmin(), 2, "getmin")
            self.assertAlmostEqual(maxi, obj.getmax(), 2, "getmax")
            self.assertAlmostEqual(mean, obj.getmean(), 2, "getmean")
            logger.info("%s %s %s" % (name, stddev, obj.getstddev()))
            self.assertAlmostEqual(stddev, obj.getstddev(), 2, "getstddev")
            self.assertEqual(dim1, obj.dim1, "dim1")
            self.assertEqual(dim2, obj.dim2, "dim2")

    def test_same(self):
        """ test if an image is the same as the EDF equivalent"""
        xsd = fabio.open(self.fn["XSDataImage.xml"])
        edf = fabio.open(self.fn["XSDataImage.edf"])
        self.assertAlmostEqual(0, abs(xsd.data - edf.data).max(), 1, "images are the same")

    def test_invert(self):
        """ Tests that 2 matrixes are invert """
        m1 = fabio.open(self.fn["XSDataImage.xml"])
        m2 = fabio.open(self.fn["XSDataImageInv.xml"])
        self.assertAlmostEqual(
        abs((numpy.matrix(m1.data) * numpy.matrix(m2.data)) - numpy.identity(m1.data.shape[0])).max(),
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

