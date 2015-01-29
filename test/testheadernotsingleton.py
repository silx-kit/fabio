#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
# Unit tests

# builds on stuff from ImageD11.test.testpeaksearch
28/11/2014
"""
from __future__ import print_function, with_statement, division, absolute_import
import unittest
import sys
import os
import numpy
import gzip
import bz2

try:
    from .utilstest import UtilsTest
except (ValueError, SystemError):
    from utilstest import UtilsTest

logger = UtilsTest.get_logger(__file__)
fabio = sys.modules["fabio"]
import shutil


class TestHeaderNotSingleton(unittest.TestCase):

    def setUp(self):
        """
        download images
        """
        self.file1 = UtilsTest.getimage("mb_LP_1_001.img.bz2")[:-4]

    def testheader(self):
        file2 = self.file1.replace("mb_LP_1_001.img", "mb_LP_1_002.img")
        self.assertTrue(os.path.exists(self.file1))
        if not os.path.exists(file2):
            shutil.copy(self.file1, file2)
        image1 = fabio.open(self.file1)
        image2 = fabio.open(file2)
        self.assertEqual(image1.header['filename'], self.file1)
        self.assertEqual(image2.header['filename'], file2)
        self.assertNotEqual(image1.header['filename'],
                             image2.header['filename'])


def test_suite_all_header():
    testSuite = unittest.TestSuite()
    testSuite.addTest(TestHeaderNotSingleton("testheader"))
    return testSuite

if __name__ == '__main__':
    mysuite = test_suite_all_header()
    runner = unittest.TextTestRunner()
    runner.run(mysuite)
