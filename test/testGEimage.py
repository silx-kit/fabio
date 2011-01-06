#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
# Unit tests

# builds on stuff from ImageD11.test.testpeaksearch
"""

import unittest, os
import logging
import sys

for idx, opts in enumerate(sys.argv[:]):
    if opts in ["-d", "--debug"]:
        logging.basicConfig(level=logging.DEBUG)
        sys.argv.pop(idx)
try:
    logging.debug("tests loaded from file: %s" % __file__)
except:
    __file__ = os.getcwd()

from utilstest import UtilsTest

from fabio.GEimage import GEimage
# filename dim1 dim2 min max mean stddev
TESTIMAGES = """GE_aSI_detector_image_1529  2048 2048 1515 16353 1833.0311 56.9124
GE_aSI_detector_image_1529.gz  2048 2048 1515 16353 1833.0311 56.9124
GE_aSI_detector_image_1529.bz2  2048 2048 1515 16353 1833.0311 56.9124"""


class testGE(unittest.TestCase):

    def setUp(self):
        """
        download images
        """
        UtilsTest.getimage("GE_aSI_detector_image_1529.bz2")


    def test_read(self):
        for line in TESTIMAGES.split("\n"):
            vals = line.split()
            name = vals[0]
            dim1, dim2 = [int(x) for x in vals[1:3]]
            mini, maxi, mean, stddev = [float(x) for x in vals[3:]]
            obj = GEimage()
            obj.read(os.path.join("testimages", name))

            self.assertAlmostEqual(mini, obj.getmin(), 2, "getmin")
            self.assertAlmostEqual(maxi, obj.getmax(), 2, "getmax")
            self.assertAlmostEqual(mean, obj.getmean(), 2, "getmean")
            self.assertAlmostEqual(stddev, obj.getstddev(), 2, "getstddev")
            self.assertEqual(dim1, obj.dim1, "dim1")
            self.assertEqual(dim2, obj.dim2, "dim2")


def test_suite_all_GE():
    testSuite = unittest.TestSuite()
    testSuite.addTest(testGE("test_read"))
    return testSuite

if __name__ == '__main__':
    mysuite = test_suite_all_GE()
    runner = unittest.TextTestRunner()
    runner.run(mysuite)
