#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
#gipped Tiff Unit tests

#built on testedfimage
"""

import unittest
import os
import logging
import sys
import gzip, bz2

for idx, opts in enumerate(sys.argv[:]):
    if opts in ["-d", "--debug"]:
        logging.basicConfig(level=logging.DEBUG)
        sys.argv.pop(idx)
try:
    logging.debug("tests loaded from file: %s" % __file__)
except:
    __file__ = os.getcwd()

from utilstest import UtilsTest
from fabio.openimage import openimage


class testgziptif(unittest.TestCase):
    def setUp(self):
        UtilsTest.getimage("oPPA_5grains_0001.tif.bz2")
        self.zipped = os.path.join("testimages",
                                   "oPPA_5grains_0001.tif.gz")
        self.unzipped = os.path.join("testimages",
                                     "oPPA_5grains_0001.tif")
#        os.system("gunzip -dc %s > %s" % (self.zipped, self.unzipped))
        assert os.path.exists(self.zipped)
        assert os.path.exists(self.unzipped)

    def test1(self):
        o1 = openimage(self.zipped)
        o2 = openimage(self.unzipped)
        self.assertEqual(o1.data[0, 0], 10)
        self.assertEqual(o2.data[0, 0], 10)


class testtif_rect(unittest.TestCase):
    def setUp(self):
        UtilsTest.getimage("testmap1_0002.tif.bz2")

    def test1(self):
        o1 = openimage(os.path.join("testimages",
                                    "testmap1_0002.tif.gz"))
        self.assertEqual(o1.data.shape, (100, 120))


def test_suite_all_tiff():
    testSuite = unittest.TestSuite()
    testSuite.addTest(testgziptif("test1"))
    testSuite.addTest(testtif_rect("test1"))
    return testSuite

if __name__ == '__main__':
    mysuite = test_suite_all_tiff()
    runner = unittest.TextTestRunner()
    runner.run(mysuite)
