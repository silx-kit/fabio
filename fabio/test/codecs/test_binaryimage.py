#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Project: Fable Input Output
#             https://github.com/silx-kit/fabio
#
#    Copyright (C) European Synchrotron Radiation Facility, Grenoble, France
#
#    Principal author:       Jérôme Kieffer (Jerome.Kieffer@ESRF.eu)
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
# THE SOFTWARE.
#

"""Test binary images
"""

import unittest
import os
import logging

logger = logging.getLogger(__name__)
import numpy
from fabio.openimage import openimage
from fabio.binaryimage import BinaryImage
from ..utilstest import UtilsTest


def make_file(name, shape, dtype):
    data = numpy.random.random(shape).astype(dtype)
    numpy.save(name, data)
    return data


class TestBinaryImage(unittest.TestCase):
    """basic test"""

    @classmethod
    def setUpClass(cls):
        cls.fn3 = os.path.join(UtilsTest.tempdir, "binary.npy")
        cls.shape = (99, 101)
        cls.dtype = "<f"
        cls.data = make_file(cls.fn3, cls.shape, cls.dtype)

    def test_read(self):
        """ check we can read images from Eiger"""
        e = BinaryImage()
        e.read(self.fn3, self.shape[1], self.shape[0], offset=-1, bytecode=self.dtype[1], endian=self.dtype[0])
        f = openimage(self.fn3)
        self.assertEqual(e.shape, f.shape)
        self.assertEqual(e.bpp, f.bpp, "bpp OK")
        print(self.fn3)
        self.assertEqual(abs(e.data-f.data).max(), 0, "data OK")
        


    def test_write(self):
        fn = os.path.join(UtilsTest.tempdir, "binary_write.h5")
        ary = numpy.random.randint(0, 100, size=self.shape)
        e = BinaryImage(data = ary)
        e.save(fn)
        self.assertTrue(os.path.exists(fn), "file exists")
        f = BinaryImage()
        f.read(fn, self.shape[1], self.shape[0], offset=0, bytecode=ary.dtype)
        self.assertEqual(str(f.__class__.__name__), "BinaryImage", "Used the write reader")
        self.assertEqual(self.shape, f.shape, "shape matches")
        self.assertEqual(abs(f.data - ary).max(), 0, "first frame matches")


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestBinaryImage))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
