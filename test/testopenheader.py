#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# Unit tests
Jerome Kieffer, 04/12/2014 
"""
from __future__ import print_function, with_statement, division, absolute_import
import unittest
import sys
import os
import numpy

try:
    from .utilstest import UtilsTest
except (ValueError, SystemError):
    from utilstest import UtilsTest

logger = UtilsTest.get_logger(__file__)
fabio = sys.modules["fabio"]
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


