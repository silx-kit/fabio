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
""" Test the fit2d mask reader

Updated by Jerome Kieffer (jerome.kieffer@esrf.eu), 2011
28/11/2014
"""
from __future__ import print_function, with_statement, division, absolute_import

import unittest
import os
import numpy
import logging

logger = logging.getLogger(__name__)

import fabio
from fabio.fit2dmaskimage import fit2dmaskimage
from ..utilstest import UtilsTest


class TestFaceMask(unittest.TestCase):
    """ test the picture of a face """

    def setUp(self):
        """
        download images
        """
        self.filename = UtilsTest.getimage("face.msk.bz2")[:-4]
        self.edffilename = UtilsTest.getimage("face.edf.bz2")[:-4]

    def test_getmatch(self):
        """ test edf and msk are the same """
        i = fit2dmaskimage()
        i.read(self.filename)
        j = fabio.open(self.edffilename)
        self.assertEqual(i.shape, j.shape)
        self.assertEqual(i.data.shape, j.data.shape)
        diff = j.data - i.data
        sumd = abs(diff).sum(dtype=float)
        self.assertEqual(sumd, 0.0)


class TestClickedMask(unittest.TestCase):
    """ A few random clicks to make a test mask """

    def setUp(self):
        """
        download images
        """
        self.filename = UtilsTest.getimage("fit2d_click.msk.bz2")[:-4]
        self.edffilename = UtilsTest.getimage("fit2d_click.edf.bz2")[:-4]

    def test_read(self):
        """ Check it reads a mask OK """
        i = fit2dmaskimage()
        i.read(self.filename)
        self.assertEqual(i.shape, (1024, 1024))
        self.assertEqual(i.bpp, 1)
        self.assertEqual(i.bytecode, numpy.uint8)
        self.assertEqual(i.data.shape, (1024, 1024))

    def test_getmatch(self):
        """ test edf and msk are the same """
        i = fit2dmaskimage()
        j = fabio.open(self.edffilename)
        i.read(self.filename)
        self.assertEqual(i.data.shape, j.data.shape)
        diff = j.data - i.data
        self.assertEqual(i.getmax(), 1)
        self.assertEqual(i.getmin(), 0)
        sumd = abs(diff).sum(dtype=float)
        self.assertEqual(sumd, 0)


class TestMskWrite(unittest.TestCase):
    """
    Write dummy mask files with various compression schemes

    """
    def setUp(self):
        shape = (199, 211)  # those are prime numbers
        self.data = (numpy.random.random(shape) > 0.6)
        self.header = fit2dmaskimage.check_header()

    def atest(self):
        e = fit2dmaskimage(data=self.data, header=self.header)
        e.write(self.filename)
        r = fabio.open(self.filename)
        self.assertEqual(e.shape, r.shape, "shape are the same")
        if r.header != self.header:
            print("Issue with header in TestMskWrite.testFlat")
            for k, v in r.header.items():
                print(k, v, self.header.get(k))
            print(e.header)
            print(r.header)
            print(self.header)

        else:
            self.assertTrue(r.header == self.header, "header are OK")
        self.assertTrue(abs(r.data - self.data).max() == 0, "data are OK")

    def testFlat(self):
        self.filename = os.path.join(UtilsTest.tempdir, "random.msk")
        self.atest()

    def testGzip(self):
        self.filename = os.path.join(UtilsTest.tempdir, "random.msk.gz")
        self.atest()

    def testBzip2(self):
        self.filename = os.path.join(UtilsTest.tempdir, "random.msk.gz")
        self.atest()

    def tearDown(self):
        if os.path.isfile(self.filename):
            os.unlink(self.filename)


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestFaceMask))
    testsuite.addTest(loadTests(TestClickedMask))
    testsuite.addTest(loadTests(TestMskWrite))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
