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
#bruker100 Unit tests

19/01/2015
"""
from __future__ import print_function, with_statement, division, absolute_import

import unittest
import os
import logging

logger = logging.getLogger(__name__)

from fabio.bruker100image import Bruker100Image
from fabio.openimage import openimage
from ..utilstest import UtilsTest

# filename dim1 dim2 min max mean stddev
TESTIMAGES = """NaCl_10_01_0009.sfrm         512 512 -30 5912 34.4626 26.189
                NaCl_10_01_0009.sfrm.gz      512 512 -30 5912 34.4626 26.189
                NaCl_10_01_0009.sfrm.bz2     512 512 -30 5912 34.4626 26.189"""
REFIMAGE = "NaCl_10_01_0009.npy.bz2"


class TestBruker100(unittest.TestCase):
    """ check some read data from bruker version100 detector"""
    def setUp(self):
        """
        download images
        """
        UtilsTest.getimage(REFIMAGE)
        self.im_dir = os.path.dirname(UtilsTest.getimage(TESTIMAGES.split()[0] + ".bz2"))

    def test_read(self):
        """ check we can read bruker100 images"""
        for line in TESTIMAGES.split("\n"):
            vals = line.split()
            name = vals[0]
            dim1, dim2 = [int(x) for x in vals[1:3]]
            shape = dim2, dim1
            mini, maxi, mean, stddev = [float(x) for x in vals[3:]]
            obj = Bruker100Image()
            obj.read(os.path.join(self.im_dir, name))
            self.assertAlmostEqual(mini, obj.getmin(), 2, "getmin")
            self.assertAlmostEqual(maxi, obj.getmax(), 2, "getmax")
            self.assertAlmostEqual(mean, obj.getmean(), 2, "getmean")
            self.assertAlmostEqual(stddev, obj.getstddev(), 2, "getstddev")
            self.assertEqual(shape, obj.shape)

    def test_same(self):
        """ check we can read bruker100 images"""
        ref = openimage(os.path.join(self.im_dir, REFIMAGE))
        for line in TESTIMAGES.split("\n"):
            obt = openimage(os.path.join(self.im_dir, line.split()[0]))
            self.assertTrue(abs(ref.data - obt.data).max() == 0, "data are the same")

    def test_write(self):
        fname = TESTIMAGES.split()[0]
        obt = openimage(os.path.join(self.im_dir, fname))
        name = os.path.basename(fname)

        obj = Bruker100Image(data=obt.data, header=obt.header)
        obj.write(os.path.join(UtilsTest.tempdir, name))
        other = openimage(os.path.join(UtilsTest.tempdir, name))
        self.assertEqual(abs(obt.data - other.data).max(), 0, "data are the same")
        for key in obt.header:
            self.assertTrue(key in other.header, "Key %s is in header" % key)
            self.assertEqual(obt.header[key], other.header[key], "value are the same for key %s" % key)
        os.unlink(os.path.join(UtilsTest.tempdir, name))


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestBruker100))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
