#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Project: Fable Input Output
#             https://github.com/kif/fabio
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

Updated by Jerome Kieffer (jerome.kieffer@esrf.eu), 2011
28/11/2014
"""

from __future__ import absolute_import, print_function, with_statement, division
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
        ds = numpy.array([0, 128])
        ref = b"\x00\x80\x80\00"
        self.assertEqual(ref, compression.compByteOffset_numpy(ds), "test +128")
        ds = numpy.array([0, -128])
        ref = b'\x00\x80\x80\xff'
        self.assertEqual(ref, compression.compByteOffset_numpy(ds), "test -128")
        ds = numpy.array([10, -128])
        ref = b'\n\x80v\xff'
        self.assertEqual(ref, compression.compByteOffset_numpy(ds), "test +10 -128")
        self.assertEqual(self.ref, compression.compByteOffset_numpy(self.ds) , "test larger")

    def testSC(self):
        """test that datasets are unchanged after various comression/decompressions"""

        obt_np = compression.decByteOffset_numpy(compression.compByteOffset_numpy(self.ds))
        self.assertEqual(abs(self.ds - obt_np).max(), 0.0, "numpy algo")
        obt_cy = compression.decByteOffset_cython(compression.compByteOffset_numpy(self.ds))
        self.assertEqual(abs(self.ds - obt_cy).max(), 0.0, "cython algo")
        obt_cy2 = compression.decByteOffset_cython(compression.compByteOffset_numpy(self.ds), self.ds.size)
        self.assertEqual(abs(self.ds - obt_cy2).max(), 0.0, "cython algo_orig")
#         obt_we = compression.decByteOffset_weave(compression.compByteOffset_numpy(self.ds), self.ds.size)
#         self.assertEqual(abs(self.ds - obt_we).max(), 0.0, "weave algo")


def suite():
    testsuite = unittest.TestSuite()
    testsuite.addTest(TestByteOffset("testSC"))
    testsuite.addTest(TestByteOffset("testComp"))
    return testsuite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())




