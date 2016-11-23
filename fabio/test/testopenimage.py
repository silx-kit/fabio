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
# Unit tests

builds on stuff from ImageD11.test.testpeaksearch
Jerome Kieffer 04/12/2014
"""
from __future__ import print_function, with_statement, division, absolute_import
import unittest
import sys
import os
import numpy

if __name__ == '__main__':
    import pkgutil
    __path__ = pkgutil.extend_path([os.path.dirname(__file__)], "fabio.test")
from .utilstest import UtilsTest


logger = UtilsTest.get_logger(__file__)
fabio = sys.modules["fabio"]

from fabio.openimage import openimage
from fabio.edfimage import edfimage
from fabio.marccdimage import marccdimage
from fabio.fit2dmaskimage import fit2dmaskimage
from fabio.OXDimage import OXDimage
from fabio.brukerimage import brukerimage
from fabio.adscimage import adscimage


class testopenedf(unittest.TestCase):
    """openimage opening edf"""
    fname = "F2K_Seb_Lyso0675.edf.bz2"
    def setUp(self):
        self.fname = UtilsTest.getimage(self.__class__.fname)

    def testcase(self):
        """ check we can read EDF image with openimage"""
        obj = openimage(self.fname)
        obj2 = edfimage()
        obj2.read(self.fname)
        self.assertEqual(obj.data[10, 10], obj2.data[10, 10])
        self.assertEqual(type(obj), type(obj2))
        self.assertEqual(abs(obj.data.astype(int) - obj2.data.astype(int)).sum(), 0)


class testedfgz(testopenedf):
    """openimage opening edf gzip"""
    fname = "F2K_Seb_Lyso0675.edf.gz"


class testedfbz2(testopenedf):
    """openimage opening edf bzip"""
    fname = "F2K_Seb_Lyso0675.edf.bz2"


class testopenmccd(unittest.TestCase):
    """openimage opening mccd"""
    fname = "somedata_0001.mccd"

    def setUp(self):
        self.fname = UtilsTest.getimage(self.__class__.fname)

    def testcase(self):
        """ check we can read it"""
        obj = openimage(self.fname)
        obj2 = marccdimage()
        obj2.read(self.fname)
        self.assertEqual(obj.data[10, 10], obj2.data[10, 10])
        self.assertEqual(type(obj), type(obj2))
        self.assertEqual(abs(obj.data.astype(int) - obj2.data.astype(int)).sum(), 0)


class testmccdgz(testopenmccd):
    """openimage opening mccd gzip"""
    fname = "somedata_0001.mccd.gz"


class testmccdbz2(testopenmccd):
    """openimage opening mccd bzip"""
    fname = "somedata_0001.mccd.bz2"


class testmask(unittest.TestCase):
    """openimage opening mccd"""
    fname = "face.msk"

    def setUp(self):
        """ check file exists """
        self.fname = UtilsTest.getimage(self.__class__.fname)

    def testcase(self):
        """ check we can read Fit2D mask with openimage"""
        obj = openimage(self.fname)
        obj2 = fit2dmaskimage()
        obj2.read(self.fname)
        self.assertEqual(obj.data[10, 10], obj2.data[10, 10])
        self.assertEqual(type(obj), type(obj2))
        self.assertEqual(abs(obj.data.astype(int) - obj2.data.astype(int)).sum(), 0)
        self.assertEqual(abs(obj.data.astype(int) - obj2.data.astype(int)).sum(), 0)


class testmaskgz(testmask):
    """openimage opening mccd gzip"""
    fname = "face.msk.gz"


class testmaskbz2(testmask):
    """openimage opening mccd bzip"""
    fname = "face.msk.bz2"


class testbruker(unittest.TestCase):
    """openimage opening bruker"""
    fname = "Cr8F8140k103.0026"

    def setUp(self):
        self.fname = UtilsTest.getimage(self.__class__.fname)

    def testcase(self):
        """ check we can read it"""
        obj = openimage(self.fname)
        obj2 = brukerimage()
        obj2.read(self.fname)
        self.assertEqual(obj.data[10, 10], obj2.data[10, 10])
        self.assertEqual(type(obj), type(obj2))
        self.assertEqual(abs(obj.data.astype(int) - obj2.data.astype(int)).sum(), 0)


class testbrukergz(testbruker):
    """openimage opening bruker gzip"""
    fname = "Cr8F8140k103.0026.gz"

class testbrukerbz2(testbruker):
    """openimage opening bruker bzip"""
    fname = "Cr8F8140k103.0026.bz2"


class testadsc(unittest.TestCase):
    """openimage opening adsc"""
    fname = os.path.join("testimages", "mb_LP_1_001.img")

    def setUp(self):
        self.fname = UtilsTest.getimage("mb_LP_1_001.img.bz2")

    def testcase(self):
        """ check we can read it"""
        obj = openimage(self.fname)
        obj2 = adscimage()
        obj2.read(self.fname)
        self.assertEqual(obj.data[10, 10], obj2.data[10, 10])
        self.assertEqual(type(obj), type(obj2))
        self.assertEqual(abs(obj.data.astype(int) - obj2.data.astype(int)).sum(), 0)


class testadscgz(testadsc):
    """openimage opening adsc gzip"""
    fname = os.path.join("testimages", "mb_LP_1_001.img.gz")


class testadscbz2(testadsc):
    """openimage opening adsc bzip"""
    fname = os.path.join("testimages", "mb_LP_1_001.img.bz2")


class testOXD(unittest.TestCase):
    """openimage opening adsc"""
    fname = "b191_1_9_1.img.bz2"

    def setUp(self):
        self.fname = UtilsTest.getimage(self.__class__.fname)[:-4]

    def testcase(self):
        """ check we can read OXD images with openimage"""
        obj = openimage(self.fname)
        obj2 = OXDimage()
        obj2.read(self.fname)
        self.assertEqual(obj.data[10, 10], obj2.data[10, 10])
        self.assertEqual(type(obj), type(obj2))
        self.assertEqual(abs(obj.data.astype(int) - obj2.data.astype(int)).sum(), 0)


class testOXDUNC(testOXD):
    """openimage opening oxd"""
    fname = "b191_1_9_1_uncompressed.img.bz2"

    def setUp(self):
        self.fname = UtilsTest.getimage(self.__class__.fname)[:-4]


def suite():
    testsuite = unittest.TestSuite()
    testsuite.addTest(testedfbz2("testcase"))
    testsuite.addTest(testopenedf("testcase"))
    testsuite.addTest(testedfgz("testcase"))

    testsuite.addTest(testmccdbz2("testcase"))
    testsuite.addTest(testopenmccd("testcase"))
    testsuite.addTest(testmccdgz("testcase"))

    testsuite.addTest(testmaskbz2("testcase"))
    testsuite.addTest(testmask("testcase"))
    testsuite.addTest(testmaskgz("testcase"))

    testsuite.addTest(testbrukerbz2("testcase"))
    testsuite.addTest(testbruker("testcase"))
    testsuite.addTest(testbrukergz("testcase"))

    testsuite.addTest(testadscbz2("testcase"))
    testsuite.addTest(testadsc("testcase"))
    testsuite.addTest(testadscgz("testcase"))

    testsuite.addTest(testOXD("testcase"))
    testsuite.addTest(testOXDUNC("testcase"))

    return testsuite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
