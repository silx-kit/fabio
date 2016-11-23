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

Test for PNM images.

Jerome Kieffer, 04/12/2014
"""
__author__ = "Jerome Kieffer"
__date__ = "05/11/2015"
import os
import sys
import unittest
import numpy
if __name__ == '__main__':
    import pkgutil
    __path__ = pkgutil.extend_path([os.path.dirname(__file__)], "fabio.test")
from .utilstest import UtilsTest

logger = UtilsTest.get_logger(__file__)
fabio = sys.modules["fabio"]
from fabio.pnmimage import pnmimage
from fabio.openimage import openimage


class TestPNM(unittest.TestCase):
    """basic test"""
    results = """image0001.pgm  1024 1024  0  28416 353.795654296875   2218.0290682517543"""

    def setUp(self):
        """Download files"""
        self.fn = {}
        for j in self.results.split("\n"):
            i = j.split()[0]
            self.fn[i] = UtilsTest.getimage(i + ".bz2")[:-4]
        for i in self.fn:
            assert os.path.exists(self.fn[i])

    def test_read(self):
        """ check we can read pnm images"""
        vals = self.results.split()
        name = vals[0]
        dim1, dim2 = [int(x) for x in vals[1:3]]
        mini, maxi, mean, stddev = [float(x) for x in vals[3:]]
        obj = openimage(self.fn[name])
        self.assertAlmostEqual(mini, obj.getmin(), 4, "getmin")
        self.assertAlmostEqual(maxi, obj.getmax(), 4, "getmax")
        self.assertAlmostEqual(mean, obj.getmean(), 4, "getmean")
        self.assertAlmostEqual(stddev, obj.getstddev(), 4, "getstddev")
        self.assertEqual(dim1, obj.dim1, "dim1")
        self.assertEqual(dim2, obj.dim2, "dim2")

    def test_write(self):
        pnmfile = os.path.join(UtilsTest.tempdir, "pnmfile.pnm")
        shape = (9, 11)
        size = shape[0] * shape[1]
        data = numpy.random.randint(0, 65000, size=size).reshape(shape)
        pnmimage(data=data).save(pnmfile)
        pnm = openimage(pnmfile)
        self.assert_(numpy.allclose(data, pnm.data), "data are the same")
        os.unlink(pnmfile)


def suite():
    testsuite = unittest.TestSuite()
    testsuite.addTest(TestPNM("test_read"))
    testsuite.addTest(TestPNM("test_write"))
    return testsuite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
