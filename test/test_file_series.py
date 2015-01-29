#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test cases for fileseries

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
from fabio.file_series import numbered_file_series, file_series


class TestRandomSeries(unittest.TestCase):
    """arbitrary series"""

    def setUp(self):
        """sets up"""
        self.fso = file_series(["first", "second", "last"])

    def testfirst(self):
        """check first"""
        self.assertEqual("first", self.fso.first())

    def testlast(self):
        """check first"""
        self.assertEqual("last", self.fso.last())

    def testjump(self):
        """check jump"""
        self.assertEqual("second", self.fso.jump(1))


class TestEdfNumbered(unittest.TestCase):
    """
    Typical sequence of edf files
    """
    def setUp(self):
        """ note extension has the . in it"""
        self.fso = numbered_file_series("mydata", 0, 10005, ".edf")

    def testfirst(self):
        """ first in series"""
        self.assertEqual(self.fso.first(), "mydata0000.edf")

    def testlast(self):
        """ last in series"""
        self.assertEqual(self.fso.last(), "mydata10005.edf")

    def testnext(self):
        """ check all in order """
        mylist = ["mydata%04d.edf" % (i) for i in range(0, 10005)]
        i = 1
        while i < len(mylist):
            self.assertEqual(mylist[i], self.fso.next())
            i += 1

    def testprevious(self):
        """ check all in order """
        mylist = ["mydata%04d.edf" % (i) for i in range(0, 10005)]
        i = 10003
        self.fso.jump(10004)
        while i > 0:
            self.assertEqual(mylist[i], self.fso.previous())
            i -= 1

    def testprevjump(self):
        """check current"""
        self.fso.jump(9999)
        self.assertEqual("mydata9999.edf", self.fso.current())
        self.assertEqual("mydata9998.edf", self.fso.previous())

    def testnextjump(self):
        """check current"""
        self.fso.jump(9999)
        self.assertEqual("mydata9999.edf", self.fso.current())
        self.assertEqual("mydata10000.edf", self.fso.next())

    def testlen(self):
        """check len"""
        self.assertEqual(self.fso.len(), 10006)  # +1 for 0000


def test_suite_all_series():
    testSuite = unittest.TestSuite()

    testSuite.addTest(TestRandomSeries("testfirst"))
    testSuite.addTest(TestRandomSeries("testlast"))
    testSuite.addTest(TestRandomSeries("testjump"))

    testSuite.addTest(TestEdfNumbered("testfirst"))
    testSuite.addTest(TestEdfNumbered("testprevious"))
    testSuite.addTest(TestEdfNumbered("testlast"))
    testSuite.addTest(TestEdfNumbered("testnext"))
    testSuite.addTest(TestEdfNumbered("testprevjump"))
    testSuite.addTest(TestEdfNumbered("testnextjump"))
    testSuite.addTest(TestEdfNumbered("testlen"))

    return testSuite

if __name__ == '__main__':

    mysuite = test_suite_all_series()
    runner = unittest.TextTestRunner()
    runner.run(mysuite)
