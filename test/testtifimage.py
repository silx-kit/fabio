#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# Tiff Unit tests

#built on testedfimage
"""

import unittest
import os
import logging
import sys
logger = logging.getLogger("testTiff")
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
from testtifgz import testtif_rect, testgziptif

class testtifimage_pilatus(unittest.TestCase):
    def setUp(self):
        self.fn = {}
        for i in ["pilatus2M.tif", "pilatus2M.edf"]:
            self.fn[i] = UtilsTest.getimage(i + ".bz2")
        for i in self.fn:
            assert os.path.exists(self.fn[i])


    def test1(self):
        """
        Testing pilatus tif bug
        """
        o1 = fabio.open(self.fn["pilatus2M.tif"]).data
        o2 = fabio.open(self.fn["pilatus2M.edf"]).data
        self.assertEqual(abs(o1 - o2).max(), 0.0)

class testtifimage_packbits(unittest.TestCase):
    def setUp(self):
        self.fn = {}
        for i in ["oPPA_5grains_0001.tif", "oPPA_5grains_0001.edf"]:
            self.fn[i] = UtilsTest.getimage(i + ".bz2")
        for i in self.fn:
            assert os.path.exists(self.fn[i])

    def test1(self):
        """
        Testing packbit comressed data tif bug
        """
        o1 = fabio.open(self.fn["oPPA_5grains_0001.tif"]).data
        o2 = fabio.open(self.fn["oPPA_5grains_0001.edf"]).data
        self.assertEqual(abs(o1 - o2).max(), 0.0)

class testtifimage_fit2d(unittest.TestCase):
    def setUp(self):
        self.fn = {}
        for i in ["fit2d.tif", "fit2d.edf"]:
            self.fn[i] = UtilsTest.getimage(i + ".bz2")
        for i in self.fn:
            assert os.path.exists(self.fn[i])

    def test1(self):
        """
        Testing packbit comressed data tif bug
        """
        o1 = fabio.open(self.fn["fit2d.tif"]).data
        o2 = fabio.open(self.fn["fit2d.edf"]).data
        self.assertEqual(abs(o1 - o2).max(), 0.0)

class testtifimage_a0009(unittest.TestCase):
    """
    test image from ??? with this error 
a0009.tif TIFF 1024x1024 1024x1024+0+0 16-bit Grayscale DirectClass 2MiB 0.000u 0:00.010
identify: a0009.tif: invalid TIFF directory; tags are not sorted in ascending order. `TIFFReadDirectory' @ tiff.c/TIFFWarnings/703.
identify: a0009.tif: TIFF directory is missing required "StripByteCounts" field, calculating from imagelength. `TIFFReadDirectory' @ tiff.c/TIFFWarnings/703.

    """
    def setUp(self):
        self.fn = {}
        for i in ["a0009.tif", "a0009.edf"]:
            self.fn[i] = UtilsTest.getimage(i + ".bz2")[:-4]
        for i in self.fn:
            assert os.path.exists(self.fn[i])

    def test1(self):
        """
        Testing packbit comressed data tif bug
        """
        o1 = fabio.open(self.fn["a0009.tif"]).data
        o2 = fabio.open(self.fn["a0009.edf"]).data
        self.assertEqual(abs(o1 - o2).max(), 0.0)


def test_suite_all_tiffimage():
    testSuite = unittest.TestSuite()
    testSuite.addTest(testtifimage_packbits("test1"))
    testSuite.addTest(testtifimage_pilatus("test1"))
    testSuite.addTest(testtifimage_fit2d("test1"))
    testSuite.addTest(testgziptif("test1"))
    testSuite.addTest(testtif_rect("test1"))
    testSuite.addTest(testtifimage_a0009("test1"))
    return testSuite

if __name__ == '__main__':
    mysuite = test_suite_all_tiffimage()
    runner = unittest.TextTestRunner()
    runner.run(mysuite)
