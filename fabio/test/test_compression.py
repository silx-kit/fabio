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
#  Permission is hereby granted, free of charge, to any person
#  obtaining a copy of this software and associated documentation files
#  (the "Software"), to deal in the Software without restriction,
#  including without limitation the rights to use, copy, modify, merge,
#  publish, distribute, sublicense, and/or sell copies of the Software,
#  and to permit persons to whom the Software is furnished to do so,
#  subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be
#  included in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
#  OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#  NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#  HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
#  WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#  OTHER DEALINGS IN THE SOFTWARE.

__authors__ = ["Jérôme Kieffer"]
__contact__ = "Jerome.Kieffer@esrf.fr"
__license__ = "MIT"
__copyright__ = "2011-2016 ESRF"
__date__ = "03/04/2020"

import unittest
import numpy
import logging

logger = logging.getLogger(__name__)

from fabio import compression


class TestByteOffset(unittest.TestCase):
    """
    test the byte offset compression and decompression
    """

    def setUp(self):
        self.ds = numpy.array([0, 1, 2, 127, 0, 1, 2, 128, 0, 1, 2, 32767, 0, 1, 2, 32768, 0, 1, 2, 2147483647, 0, 1, 2, 2147483648, 0, 1, 2, 128, 129, 130, 32767, 32768, 128, 129, 130, 32768, 2147483647, 2147483648])
        self.ref = b'\x00\x01\x01}\x81\x01\x01~\x80\x80\xff\x01\x01\x80\xfd\x7f\x80\x01\x80\x01\x01\x80\xfe\x7f\x80\x00\x80\x00\x80\xff\xff\x01\x01\x80\x00\x80\xfd\xff\xff\x7f\x80\x00\x80\x01\x00\x00\x80\x01\x01\x80\x00\x80\xfe\xff\xff\x7f\x80\x00\x80\x00\x00\x00\x80\x00\x00\x00\x80\xff\xff\xff\xff\x01\x01~\x01\x01\x80}\x7f\x01\x80\x80\x80\x01\x01\x80~\x7f\x80\x00\x80\xff\x7f\xff\x7f\x01'

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        self.ds = self.ref = None

    def testComp(self):
        """
        """
        # first with numpy
        ds = numpy.array([0, 128])
        ref = b"\x00\x80\x80\00"
        self.assertEqual(ref, compression.compByteOffset_numpy(ds), "test +128")
        ds = numpy.array([0, -128])
        ref = b'\x00\x80\x80\xff'
        self.assertEqual(ref, compression.compByteOffset_numpy(ds), "test -128")
        ds = numpy.array([10, -128])
        ref = b'\n\x80v\xff'
        self.assertEqual(ref, compression.compByteOffset_numpy(ds), "test +10 -128")
        self.assertEqual(self.ref, compression.compByteOffset_numpy(self.ds), "test larger")

        # Then with cython 32 bits
        ds = numpy.array([0, 128], dtype="int32")
        ref = b"\x00\x80\x80\00"
        self.assertEqual(ref, compression.compByteOffset_cython(ds), "test +128")
        ds = numpy.array([0, -128], dtype="int32")
        ref = b'\x00\x80\x80\xff'
        self.assertEqual(ref, compression.compByteOffset_cython(ds), "test -128")
        ds = numpy.array([10, -128], dtype="int32")
        ref = b'\n\x80v\xff'
        self.assertEqual(ref, compression.compByteOffset_cython(ds), "test +10 -128")
        self.assertEqual(self.ref, compression.compByteOffset_cython(self.ds), "test larger")

        # Then with cython 64bits
        ds = numpy.array([0, 128], dtype="int64")
        ref = b"\x00\x80\x80\00"
        self.assertEqual(ref, compression.compByteOffset_cython(ds), "test +128")
        ds = numpy.array([0, -128], dtype="int64")
        ref = b'\x00\x80\x80\xff'
        self.assertEqual(ref, compression.compByteOffset_cython(ds), "test -128")
        ds = numpy.array([10, -128], dtype="int64")
        ref = b'\n\x80v\xff'
        self.assertEqual(ref, compression.compByteOffset_cython(ds), "test +10 -128")
        self.assertEqual(self.ref, compression.compByteOffset_cython(self.ds), "test larger")

    def testSC(self):
        """test that datasets are unchanged after various compression/decompressions"""

        obt_np = compression.decByteOffset_numpy(compression.compByteOffset_numpy(self.ds))
        self.assertEqual(abs(self.ds - obt_np).max(), 0.0, "numpy-numpy algo")
        obt_cy = compression.decByteOffset_cython(compression.compByteOffset_numpy(self.ds))
        self.assertEqual(abs(self.ds - obt_cy).max(), 0.0, "cython-numpy algo")
        obt_cy2 = compression.decByteOffset_cython(compression.compByteOffset_numpy(self.ds), self.ds.size)
        self.assertEqual(abs(self.ds - obt_cy2).max(), 0.0, "cython2-numpy algo_orig")

        obt_np = compression.decByteOffset_numpy(compression.compByteOffset_cython(self.ds))
        self.assertEqual(abs(self.ds - obt_np).max(), 0.0, "numpy-numpy algo")
        obt_cy = compression.decByteOffset_cython(compression.compByteOffset_cython(self.ds))
        self.assertEqual(abs(self.ds - obt_cy).max(), 0.0, "cython-numpy algo")
        obt_cy2 = compression.decByteOffset_cython(compression.compByteOffset_cython(self.ds), self.ds.size)
        self.assertEqual(abs(self.ds - obt_cy2).max(), 0.0, "cython2-numpy algo_orig")


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestByteOffset))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
