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
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE
#

"""
# Unit tests for OXD image (Oxford diffraction now Rigaku)
"""

__author__ = "Jerome Kieffer"
__license__ = "MIT"
__date__ = "03/04/2020"
__contact__ = "jerome.kieffer@esrf.fr"

import unittest
import os
import logging

logger = logging.getLogger(__name__)

import fabio
from fabio.OXDimage import OXDimage
from ..utilstest import UtilsTest

# filename dim1 dim2 min max mean stddev values are from OD Sapphire 3.0
TESTIMAGES = [
    ("b191_1_9_1.img", 512, 512, -500, 11975, 25.70, 90.2526, "Sapphire2"),
    ("b191_1_9_1_uncompressed.img", 512, 512, -500, 11975, 25.70, 90.2526, "Sapphire2"),
    ("100nmfilmonglass_1_1.img", 1024, 1024, -172, 460, 44.20, 63.0245, "Sapphire3"),
    ("pilatus300k.rod_img", 487, 619, -2, 173075, 27.315, 538.938, "Pilatus")]


class TestOxd(unittest.TestCase):

    def setUp(self):
        self.fn = {}
        for vals in TESTIMAGES:
            name = vals[0]
            self.fn[name] = UtilsTest.getimage(name + ".bz2")[:-4]
        for i in self.fn:
            assert os.path.exists(self.fn[i])

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        self.fn = {}

    def test_read(self):
        "Test reading of compressed OXD images"
        for vals in TESTIMAGES:
            name = vals[0]
            dim1, dim2 = vals[1:3]
            shape = dim2, dim1
            mini, maxi, mean, stddev = vals[3:7]
            detector_type = vals[7]
            obj = OXDimage()
            obj.read(self.fn[name])

            self.assertEqual(shape, obj.shape)

            self.assertAlmostEqual(mini, obj.getmin(), 2, "getmin on " + name)
            self.assertAlmostEqual(maxi, obj.getmax(), 2, "getmax on " + name)
            self.assertAlmostEqual(mean, obj.getmean(), 2, "getmean on " + name)
            self.assertAlmostEqual(stddev, obj.getstddev(), 2, "getstddev on " + name)

            self.assertIn(detector_type, obj.header["Detector type"], "detector type on " + name)

    def test_write(self):
        "Test writing with self consistency at the fabio level"
        for vals in TESTIMAGES:
            name = vals[0]
            obj = OXDimage()
            obj.read(self.fn[name])
            if obj.header.get("Compression") not in ["NO ", "TY1"]:
                logger.info("Skip write test for now")
                continue
            obj.write(os.path.join(UtilsTest.tempdir, name))
            other = OXDimage()
            other.read(os.path.join(UtilsTest.tempdir, name))
            self.assertEqual(abs(obj.data - other.data).max(), 0, "data are not the same for %s" % name)
            for key in obj.header:
                if key == "filename":
                    continue
                self.assertTrue(key in other.header, "Key %s is in header" % key)
                self.assertEqual(obj.header[key], other.header[key], "metadata '%s' are not the same for %s" % (key, name))

            os.unlink(os.path.join(UtilsTest.tempdir, name))


class TestOxdSame(unittest.TestCase):

    def setUp(self):
        self.fn = {}
        for i in ["b191_1_9_1.img", "b191_1_9_1_uncompressed.img"]:
            self.fn[i] = UtilsTest.getimage(i + ".bz2")[:-4]
        for i in self.fn:
            assert os.path.exists(self.fn[i])

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        self.fn = {}

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

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        self.fn = {}

    def test_same(self):
        df = [fabio.open(i).data for i in self.fn.values()]
        self.assertEqual(abs(df[0] - df[1]).max(), 0, "Data are the same")


class TestConvert(unittest.TestCase):

    def setUp(self):
        self.fn = {}
        for i in ["face.msk"]:
            self.fn[i] = UtilsTest.getimage(i + ".bz2")[:-4]
        for i in self.fn:
            self.assertTrue(os.path.exists(self.fn[i]), self.fn[i])

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        self.fn = {}

    def test_convert(self):
        fn = self.fn["face.msk"]
        dst = os.path.join(UtilsTest.tempdir, "face.oxd")
        fabio.open(fn).convert("oxd").save(dst)
        self.assertTrue(os.path.exists(dst), "destination file exists")
        os.unlink(dst)


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestOxd))
    testsuite.addTest(loadTests(TestOxdSame))
    testsuite.addTest(loadTests(TestOxdBig))
    testsuite.addTest(loadTests(TestConvert))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
