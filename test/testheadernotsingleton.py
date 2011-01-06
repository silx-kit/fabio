#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
# Unit tests

# builds on stuff from ImageD11.test.testpeaksearch
"""

import unittest
import os
import logging
import sys
import shutil

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

class testheadernotsingleton(unittest.TestCase):

    def setUp(self):
        """
        download images
        """
        UtilsTest.getimage("mb_LP_1_001.img.bz2")


    def testheader(self):
        file1 = os.path.join("testimages", "mb_LP_1_001.img")
        file2 = os.path.join("testimages", "mb_LP_1_002.img")
        self.assertTrue(os.path.exists(file1))
        if not os.path.exists(file2):
            shutil.copy(file1, file2)
        image1 = openimage(file1)
        image2 = openimage(file2)
        # print i1.header, i2.header
        self.assertEqual(image1.header['filename'] , file1)
        self.assertEqual(image2.header['filename'] , file2)
        self.assertNotEqual(image1.header['filename'] ,
                             image2.header['filename'])

def test_suite_all_header():
    testSuite = unittest.TestSuite()
    testSuite.addTest(testheadernotsingleton("testheader"))
    return testSuite

if __name__ == '__main__':
    mysuite = test_suite_all_header()
    runner = unittest.TextTestRunner()
    runner.run(mysuite)
