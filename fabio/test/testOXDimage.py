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

# builds on stuff from ImageD11.test.testpeaksearch
08/01/2015
"""
from __future__ import print_function, with_statement, division, absolute_import
import unittest
import sys
import os

if __name__ == '__main__':
    import pkgutil
    __path__ = pkgutil.extend_path([os.path.dirname(__file__)], "fabio.test")
from .utilstest import UtilsTest


logger = UtilsTest.get_logger(__file__)
fabio = sys.modules["fabio"]
from fabio.OXDimage import OXDimage


# filename dim1 dim2 min max mean stddev values are from OD Sapphire 3.0
TESTIMAGES = """b191_1_9_1.img  512 512 -500 11975 25.70 90.2526
                b191_1_9_1_uncompressed.img  512 512 -500 11975 25.70 90.2526"""


class TestOxd(unittest.TestCase):
    def setUp(self):
        self.fn = {}
        for i in ["b191_1_9_1.img", "b191_1_9_1_uncompressed.img"]:
            self.fn[i] = UtilsTest.getimage(i + ".bz2")[:-4]
        for i in self.fn:
            assert os.path.exists(self.fn[i])

    def test_read(self):
        "Test reading of compressed OXD images"
        for line in TESTIMAGES.split("\n"):
            vals = line.split()
            name = vals[0]
            dim1, dim2 = [int(x) for x in vals[1:3]]
            mini, maxi, mean, stddev = [float(x) for x in vals[3:]]
            obj = OXDimage()
            obj.read(self.fn[name])

            self.assertAlmostEqual(mini, obj.getmin(), 2, "getmin")
            self.assertAlmostEqual(maxi, obj.getmax(), 2, "getmax")
            self.assertAlmostEqual(mean, obj.getmean(), 2, "getmean")
            self.assertAlmostEqual(stddev, obj.getstddev(), 2, "getstddev")
            self.assertEqual(dim1, obj.dim1, "dim1")
            self.assertEqual(dim2, obj.dim2, "dim2")

    def test_write(self):
        "Test writing with self consistency at the fabio level"
        for line in TESTIMAGES.split("\n"):
            vals = line.split()
            name = vals[0]
            obj = OXDimage()
            obj.read(self.fn[name])
            obj.write(os.path.join(UtilsTest.tempdir, name))
            other = OXDimage()
            other.read(os.path.join(UtilsTest.tempdir, name))
            self.assertEqual(abs(obj.data - other.data).max(), 0, "data are the same for %s" % name)
            for key in obj.header:
                if key == "filename":
                    continue
                self.assertTrue(key in other.header, "Key %s is in header" % key)
                self.assertEqual(obj.header[key], other.header[key], "value are the same for key %s" % key)

            os.unlink(os.path.join(UtilsTest.tempdir, name))


class TestOxdSame(unittest.TestCase):
    def setUp(self):
        self.fn = {}
        for i in ["b191_1_9_1.img", "b191_1_9_1_uncompressed.img"]:
            self.fn[i] = UtilsTest.getimage(i + ".bz2")[:-4]
        for i in self.fn:
            assert os.path.exists(self.fn[i])

    def test_same(self):
        """test if images are actually the same"""
        o1 = fabio.open(self.fn["b191_1_9_1.img"])
        o2 = fabio.open(self.fn["b191_1_9_1_uncompressed.img"])
        for attr in ["getmin", "getmax", "getmean", "getstddev"]:
            a1 = getattr(o1, attr)()
            a2 = getattr(o2, attr)()
            self.assertEqual(a1, a2, "testing %s: %s | %s" % (attr, a1, a2))


class TestOxdBig(unittest.TestCase):
    """class to test bugs if OI is large (lot of exceptions 16 bits)"""
    def setUp(self):
        self.fn = {}
        for i in ["d80_60s.img", "d80_60s.edf"]:
            self.fn[i] = UtilsTest.getimage(i + ".bz2")[:-4]
        for i in self.fn:
            self.assertTrue(os.path.exists(self.fn[i]), self.fn[i])

    def test_same(self):
        df = [fabio.open(i).data for i in self.fn.values()]
        self.assertEqual(abs(df[0] - df[1]).max(), 0, "Data are the same")


def suite():
    testsuite = unittest.TestSuite()
    testsuite.addTest(TestOxd("test_read"))
    testsuite.addTest(TestOxd("test_write"))
    testsuite.addTest(TestOxdSame("test_same"))
    testsuite.addTest(TestOxdBig("test_same"))
    return testsuite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
