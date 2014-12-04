#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
#gipped Tiff Unit tests

#built on testedfimage
"""

from __future__ import print_function, with_statement, division
import unittest
import sys
import os
try:
    from .utilstest import UtilsTest
except ValueError:
    from utilstest import UtilsTest
logger = UtilsTest.get_logger(__file__)
fabio = sys.modules["fabio"]


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
