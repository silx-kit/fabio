#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Project: Fable Input Output
#             https://github.com/silx-kit/fabio
#
#    Copyright (C) European Synchrotron Radiation Facility, Grenoble, France
#
#    Principal author:       Jérôme Kieffer (Jerome.Kieffer@ESRF.eu)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

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

if __name__ == '__main__':
    import pkgutil
    __path__ = pkgutil.extend_path([os.path.dirname(__file__)], "fabio.test")
from .utilstest import UtilsTest

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


def suite():
    testsuite = unittest.TestSuite()
    testsuite.addTest(TestRandomSeries("testfirst"))
    testsuite.addTest(TestRandomSeries("testlast"))
    testsuite.addTest(TestRandomSeries("testjump"))

    testsuite.addTest(TestEdfNumbered("testfirst"))
    testsuite.addTest(TestEdfNumbered("testprevious"))
    testsuite.addTest(TestEdfNumbered("testlast"))
    testsuite.addTest(TestEdfNumbered("testnext"))
    testsuite.addTest(TestEdfNumbered("testprevjump"))
    testsuite.addTest(TestEdfNumbered("testnextjump"))
    testsuite.addTest(TestEdfNumbered("testlen"))

    return testsuite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
