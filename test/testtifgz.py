#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
#gipped Tiff Unit tests

#built on testedfimage
"""

import unittest, sys, os, logging
logger = logging.getLogger("testtifgz")
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


class testgziptif(unittest.TestCase):
    def setUp(self):
        self.unzipped = UtilsTest.getimage("oPPA_5grains_0001.tif.bz2")[:-4]
        self.zipped = self.unzipped + ".gz"
        assert os.path.exists(self.zipped)
        assert os.path.exists(self.unzipped)

    def test1(self):
        o1 = fabio.open(self.zipped)
        o2 = fabio.open(self.unzipped)
        self.assertEqual(o1.data[0, 0], 10)
        self.assertEqual(o2.data[0, 0], 10)


class testtif_rect(unittest.TestCase):
    def setUp(self):
        self.fn = UtilsTest.getimage("testmap1_0002.tif.bz2")[:-4]

    def test1(self):
        for ext in ["", ".gz", ".bz2"]:
            o1 = fabio.open(self.fn + ext)
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
