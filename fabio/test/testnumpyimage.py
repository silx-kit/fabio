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
Test for numpy images.
"""
__author__ = "Jérôme Kieffer"
__date__ = "16/06/2016"
import os
import sys
import unittest
if __name__ == '__main__':
    import pkgutil
    __path__ = pkgutil.extend_path([os.path.dirname(__file__)], "fabio.test")
from .utilstest import UtilsTest
import numpy
logger = UtilsTest.get_logger(__file__)
fabio = sys.modules["fabio"]
from fabio.numpyimage import NumpyImage
from fabio.openimage import openimage


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
        self.assertEqual(9, obj.dim1, "dim1")
        self.assertEqual(11, obj.dim2, "dim2")
        self.assert_(numpy.allclose(obj.data, self.ary), "data")

    def test_write(self):
        """ check we can write numpy images"""
        ref = NumpyImage(data=self.ary)
        ref.save(self.fn2)
        obj = openimage(self.fn2)
        self.assertEqual(obj.bytecode, numpy.uint16, msg="bytecode is OK")
        self.assertEqual(9, obj.dim1, "dim1")
        self.assertEqual(11, obj.dim2, "dim2")
        self.assert_(numpy.allclose(obj.data, self.ary), "data")

    def test_multidim(self):
        for shape in (10,), (10, 15), (10, 15, 20), (10, 15, 20, 25):
            ary = numpy.random.random(shape).astype("float32")
            numpy.save(self.fn, ary)
            obj = openimage(self.fn)

            self.assertEqual(obj.bytecode, numpy.float32, msg="bytecode is OK")
            self.assertEqual(shape[-1], obj.dim1, "dim1")
            dim2 = 1 if len(shape) == 1 else shape[-2]
            self.assertEqual(dim2, obj.dim2, "dim2")
            nframes = 1
            if len(shape) > 2:
                for i in shape[:-2]:
                    nframes *= i
            self.assertEqual(nframes, obj.nframes, "nframes")
            if os.path.exists(self.fn):
                os.unlink(self.fn)


def suite():
    testsuite = unittest.TestSuite()
    testsuite.addTest(TestNumpy("test_read"))
    testsuite.addTest(TestNumpy("test_write"))
    testsuite.addTest(TestNumpy("test_multidim"))
    return testsuite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
