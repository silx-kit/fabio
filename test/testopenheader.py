#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
# Unit tests
"""

import unittest
import os
import logging
import sys

force_build = False

for idx, opts in enumerate(sys.argv[:]):
    if opts in ["-d", "--debug"]:
        logging.basicConfig(level=logging.DEBUG)
        sys.argv.pop(idx)
    elif opts in ["-f", "--force"]:
        force_build = True
        sys.argv.pop(sys.argv.index(opts))

try:
    logging.debug("tests loaded from file: %s" % __file__)
except:
    __file__ = os.getcwd()

from utilstest import UtilsTest

if force_build:
    UtilsTest.forceBuild()

from fabio.openimage import openheader

NAMES = [
    os.path.join("testimages", "F2K_Seb_Lyso0675_header_only.edf.gz"),
    os.path.join("testimages", "F2K_Seb_Lyso0675_header_only.edf.bz2"),
    os.path.join("testimages", "F2K_Seb_Lyso0675_header_only.edf")
    ]


class test1(unittest.TestCase):
    """openheader opening edf"""
    def setUp(self):
        UtilsTest.getimage("F2K_Seb_Lyso0675_header_only.edf.bz2")

    def testcase(self):
        """ check openheader can read edf headers"""
        for name in NAMES:
            obj = openheader(name)
            logging.debug(" %s obj = %s" % (name, obj.header))
            self.assertEqual(obj.header["title"],
                             "ESPIA FRELON Image",
                             "Error on " + name)



def test_suite_all_openheader():
    testSuite = unittest.TestSuite()
    testSuite.addTest(test1("testcase"))
    return testSuite

if __name__ == '__main__':
    mysuite = test_suite_all_openheader()
    runner = unittest.TextTestRunner()
    runner.run(mysuite)


