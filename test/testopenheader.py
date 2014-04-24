#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# Unit tests
"""

import unittest, sys, os, logging
logger = logging.getLogger("testopenheader")
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
from fabio.openimage import openheader


class test1(unittest.TestCase):
    """openheader opening edf"""
    def setUp(self):
        self.name = UtilsTest.getimage("F2K_Seb_Lyso0675_header_only.edf.bz2")[:-4]

    def testcase(self):
        """ check openheader can read edf headers"""
        for ext in ["", ".bz2", ".gz"]:
            name = self.name + ext
            obj = openheader(name)
            logger.debug(" %s obj = %s" % (name, obj.header))
            self.assertEqual(obj.header["title"],
                             "ESPIA FRELON Image",
                             "Error on file %s" % name)



def test_suite_all_openheader():
    testSuite = unittest.TestSuite()
    testSuite.addTest(test1("testcase"))
    return testSuite

if __name__ == '__main__':
    mysuite = test_suite_all_openheader()
    runner = unittest.TextTestRunner()
    runner.run(mysuite)


