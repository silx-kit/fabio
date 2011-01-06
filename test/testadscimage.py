#!/usr/bin/env python
# -*- coding: utf8 -*-

"""
# Unit tests

# builds on stuff from ImageD11.test.testpeaksearch

Updated by Jerome Kieffer (jerome.kieffer@esrf.eu), 2011
"""
import unittest, os
import numpy as N
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
from fabio.adscimage import adscimage
from fabio.edfimage import edfimage


# statistics come from fit2d I think
# filename dim1 dim2 min max mean stddev
TESTIMAGES = """mb_LP_1_001.img 3072 3072 0.0000 65535. 120.33 147.38 
mb_LP_1_001.img.gz  3072 3072 0.0000 65535.  120.33 147.38 
mb_LP_1_001.img.bz2 3072 3072 0.0000 65535.  120.33 147.38 """



class testmatch(unittest.TestCase):
    """ check the fit2d conversion to edf gives same numbers """
    def setUp(self):
        """ Download images """
        UtilsTest.getimage("mb_LP_1_001.img.bz2")
        UtilsTest.getimage("mb_LP_1_001.edf.bz2")

    def testsame(self):
        """test ADSC image match to EDF"""
        im1 = edfimage()
        im1.read("testimages/mb_LP_1_001.edf")
        im2 = adscimage()
        im2.read("testimages/mb_LP_1_001.img")
        diff = (im1.data.astype("int32") - im2.data.astype("int32")).ravel()
        logging.info("type: %s %s shape %s %s " % (im1.data.dtype, im2.data.dtype, im1.data.shape, im2.data.shape))
        logging.info("im1 min %s %s max %s %s " % (im1.data.min(), im2.data.min(), im1.data.max(), im2.data.max()))
        logging.info("delta min %s max %s mean %s" % (diff.min(), diff.max(), diff.mean()))
        self.assertAlmostEqual(N.max(diff), 0, 2)
        self.assertAlmostEqual(N.min(diff), 0, 2)

class testflatmccdsadsc(unittest.TestCase):
    """
    """
    def test_read(self):
        """ check we can read flat ADSC images"""
        for line in TESTIMAGES.split("\n"):
            vals = line.split()
            name = vals[0]
            dim1, dim2 = [int(x) for x in vals[1:3]]
            mini, maxi, mean, stddev = [float(x) for x in vals[3:]]
            obj = adscimage()
            obj.read(os.path.join("testimages", name))
            self.assertAlmostEqual(mini, obj.getmin(), 2, "getmin")
            self.assertAlmostEqual(maxi, obj.getmax(), 2, "getmax")
            self.assertAlmostEqual(mean, obj.getmean(), 2, "getmean")
            self.assertAlmostEqual(stddev, obj.getstddev(), 2, "getstddev")
            self.assertEqual(dim1, obj.dim1, "dim1")
            self.assertEqual(dim2, obj.dim2, "dim2")






def test_suite_all_adsc():
    testSuite = unittest.TestSuite()
    testSuite.addTest(testmatch("testsame"))
    testSuite.addTest(testflatmccdsadsc("test_read"))
    return testSuite

if __name__ == '__main__':
    mysuite = test_suite_all_adsc()
    runner = unittest.TextTestRunner()
    runner.run(mysuite)



