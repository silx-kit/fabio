#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
# Unit tests

# builds on stuff from ImageD11.test.testpeaksearch
"""

import unittest, sys, os, logging
logger = logging.getLogger("testheadernotsingleton")
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
import shutil

class testheadernotsingleton(unittest.TestCase):

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
        self.assertEqual(image1.header['filename'] , self.file1)
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
