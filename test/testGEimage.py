#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# Unit tests

# builds on stuff from ImageD11.test.testpeaksearch
"""

import unittest, sys, os, logging
logger = logging.getLogger("testfit2dmaskdfimage")
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
from fabio.GEimage import GEimage
# filename dim1 dim2 min max mean stddev
TESTIMAGES = """GE_aSI_detector_image_1529      2048 2048 1515 16353 1833.0311 56.9124
                GE_aSI_detector_image_1529.gz   2048 2048 1515 16353 1833.0311 56.9124
                GE_aSI_detector_image_1529.bz2  2048 2048 1515 16353 1833.0311 56.9124"""


class testGE(unittest.TestCase):

    def setUp(self):
        """
        download images
        """
        self.GE = UtilsTest.getimage("GE_aSI_detector_image_1529.bz2")


    def test_read(self):
        for line in TESTIMAGES.split("\n"):
            vals = line.split()
            name = vals[0]
            dim1, dim2 = [int(x) for x in vals[1:3]]
            mini, maxi, mean, stddev = [float(x) for x in vals[3:]]
            obj = GEimage()
            obj.read(os.path.join(os.path.dirname(self.GE), name))

            self.assertAlmostEqual(mini, obj.getmin(), 4, "getmin")
            self.assertAlmostEqual(maxi, obj.getmax(), 4, "getmax")
            self.assertAlmostEqual(mean, obj.getmean(), 4, "getmean")
            self.assertAlmostEqual(stddev, obj.getstddev(), 4, "getstddev")
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
