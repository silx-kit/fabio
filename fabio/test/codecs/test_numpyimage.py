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
# THE SOFTWARE.
#
"""
Test for numpy images.
"""
__author__ = "Jérôme Kieffer"
__date__ = "03/04/2020"

import os
import unittest
import numpy
import logging

logger = logging.getLogger(__name__)

from fabio.numpyimage import NumpyImage
from fabio.openimage import openimage
from ..utilstest import UtilsTest


class TestNumpy(unittest.TestCase):
    """basic test"""

    def setUp(self):
        """Generate files"""

        self.ary = numpy.random.randint(0, 6500, size=99).reshape(11, 9).astype("uint16")
        self.fn = os.path.join(UtilsTest.tempdir, "numpy.npy")
        self.fn2 = os.path.join(UtilsTest.tempdir, "numpy2.npy")
        numpy.save(self.fn, self.ary)

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        for i in (self.fn, self.fn2):
            if os.path.exists(i):
                os.unlink(i)
        self.ary = self.fn = self.fn2 = None

    def test_read(self):
        """ check we can read pnm images"""
        obj = openimage(self.fn)

        self.assertEqual(obj.bytecode, numpy.uint16, msg="bytecode is OK")
        self.assertEqual(obj.shape, (11, 9))
        self.assertTrue(numpy.allclose(obj.data, self.ary), "data")

    def test_write(self):
        """ check we can write numpy images"""
        ref = NumpyImage(data=self.ary)
        ref.save(self.fn2)
        with openimage(self.fn2) as obj:
            self.assertEqual(obj.bytecode, numpy.uint16, msg="bytecode is OK")
            self.assertEqual(obj.shape, (11, 9))
            self.assertTrue(numpy.allclose(obj.data, self.ary), "data")

    def test_multidim(self):
        for shape in (10,), (10, 15), (10, 15, 20), (10, 15, 20, 25):
            ary = numpy.random.random(shape).astype("float32")
            numpy.save(self.fn, ary)
            with openimage(self.fn) as obj:
                self.assertEqual(obj.bytecode, numpy.float32, msg="bytecode is OK")
                self.assertEqual(shape[-1], obj.shape[-1], "dim1")
                dim2 = 1 if len(shape) == 1 else shape[-2]
                self.assertEqual(dim2, obj.shape[-2], "dim2")
                nframes = 1
                if len(shape) > 2:
                    for i in shape[:-2]:
                        nframes *= i
                    # print(shape,nframes, obj.nframes)
                    self.assertEqual(nframes, obj.nframes, "nframes")
            if os.path.exists(self.fn):
                os.unlink(self.fn)


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestNumpy))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
