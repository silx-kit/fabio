#!/usr/bin/env python
# coding: utf-8
#
#    Project: FabIO tests class utilities
#
#    Copyright (C) 2010-2016 European Synchrotron Radiation Facility
#                       Grenoble, France
#
#    Principal authors: Jérôme KIEFFER (jerome.kieffer@esrf.fr)
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
__author__ = "Jérôme Kieffer"
__contact__ = "jerome.kieffer@esrf.eu"
__license__ = "MIT"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__date__ = "13/11/2020"

import io
import logging
import unittest
from struct import pack

import numpy as np

from ..compression import agi_bitfield
from ..ext import _agi_bitfield

logger = logging.getLogger(__name__)


class TestUtil(unittest.TestCase):

    def test_get_fieldsize(self):
        test_cases = [
            (np.zeros(8, dtype="int32"), 1),
            (np.array([1024] * 8, dtype="int32"), 8),
            (np.arange(0, 7, dtype="int32"), 4),
            (np.array([-1, -2, 2, 1] * 2, dtype="int32"), 3),
            (np.array([-3, 3, 8, 3, -5 - 5, 0, 6]), 5)
        ]
        for array, result in test_cases:
            fs = agi_bitfield.get_fieldsize(array)
            self.assertEqual(result, fs)
            fs = _agi_bitfield.get_fieldsize(array)
            self.assertEqual(result, fs)

    def test_compress_decode_field_overflow(self):
        data = np.array([1, 2, 3, 4, 255, 40000, -4, 2], dtype="int32")
        fs = agi_bitfield.get_fieldsize(data)

        oft = io.BytesIO()
        cf = agi_bitfield.compress_field(data, fs, oft)
        self.assertEqual(pack("h", 255) + pack("i", 40000), oft.getvalue())

        mask_ = agi_bitfield.MASK[fs]
        dec = agi_bitfield.decode_field(cf)
        self.assertEqual([1 + 127, 2 + 127, 3 + 127, 4 + 127, 0xfe & mask_, 0xff & mask_, -4 + 127, 2 + 127], dec)

    def test_compress_decompress_field_small(self):
        data = np.array([1, 0] * 4, dtype="int32")
        fs = agi_bitfield.get_fieldsize(data)

        oft = io.BytesIO()
        cf = agi_bitfield.compress_field(data, fs, oft)
        self.assertEqual(b'', oft.getvalue())

        conv_ = agi_bitfield.MASK[fs - 1]
        dec = agi_bitfield.decode_field(cf[:fs])
        self.assertEqual([1 + conv_, 0 + conv_] * 4, dec)

    def test_full_compress_decompress_field(self):
        data = np.array([1, 2, 3, 4, 255, -40000, -4, 2], dtype="int32")
        fs = agi_bitfield.get_fieldsize(data)

        oft = io.BytesIO()
        cf = agi_bitfield.compress_field(data, fs, oft)

        oft = io.BytesIO(oft.getvalue())  # do this to simulate actual conditions. the data is passed between
        # encoding and decoding as bytes so the index would not be preserved

        field = agi_bitfield.decode_field(cf[:fs])
        agi_bitfield.undo_escapes(field, fs, oft)
        self.assertEqual(list(data), field)

    def test_mask_conv(self):
        mask_cases = [
            (1, 1),
            (4, 0b1111),
            (8, 0xff)
        ]
        for length, msk in mask_cases:
            self.assertEqual(msk, agi_bitfield.MASK[length])
        conv_cases = [
            (1, 0),
            (4, 0b111),
            (8, 0b1111111)
        ]
        for length, cnv in conv_cases:
            self.assertEqual(cnv, agi_bitfield.MASK[length - 1])


class TestRow(unittest.TestCase):

    def test_compress_row_zero(self):
        data = np.zeros(256, dtype="int32")
        buffer = io.BytesIO()
        buffer_python = io.BytesIO()
        buffer_cython = io.BytesIO()
        _agi_bitfield.compress_row(data, buffer_cython)
        agi_bitfield.compress_row(data, buffer_python)
        self.assertEqual(buffer_cython.getbuffer(), buffer_python.getbuffer(), "compressed string matches")
        _agi_bitfield.compress_row(data, buffer)
        buffer.seek(0)
        decompressed = agi_bitfield.decompress_row(buffer, 256)
        decompressed = np.array(decompressed, dtype="int32").cumsum()
        self.assertTrue(np.array_equal(decompressed, data))

    def test_compress_row_small(self):
        data = np.random.randint(0, 5, 256, dtype="int32")
        buffer = io.BytesIO()
        buffer_python = io.BytesIO()
        buffer_cython = io.BytesIO()
        _agi_bitfield.compress_row(data, buffer_cython)
        agi_bitfield.compress_row(data, buffer_python)
        self.assertEqual(buffer_cython.getbuffer(), buffer_python.getbuffer(), "compressed string matches")
        _agi_bitfield.compress_row(data, buffer)
        buffer.seek(0)
        decompressed = agi_bitfield.decompress_row(buffer, 256)
        decompressed = np.array(decompressed, dtype="int32").cumsum()
        self.assertTrue(np.array_equal(decompressed, data))

    def compress_row_overflows(self):
        data = np.random.randint(-255, 255, 256, dtype="int32")
        buffer = io.BytesIO()
        buffer_python = io.BytesIO()
        buffer_cython = io.BytesIO()
        _agi_bitfield.compress_row(data, buffer_cython)
        agi_bitfield.compress_row(data, buffer_python)
        self.assertEqual(buffer_cython.getbuffer(), buffer_python.getbuffer(), "compressed string matches")
        _agi_bitfield.compress_row(data, buffer)
        buffer.seek(0)
        decompressed = agi_bitfield.decompress_row(buffer, 256)
        decompressed = np.array(decompressed, dtype="int32").cumsum()
        self.assertTrue(np.array_equal(decompressed, data))


class TestCompression(unittest.TestCase):

    def test_full_rand(self):
        data = np.random.randint(-256, 500, (256, 256)).astype("int32")
        import time
        t0 = time.perf_counter()
        compressed = agi_bitfield.compress(data)
        t1 = time.perf_counter()
        uncompressed = agi_bitfield.decompress(compressed, data.shape)
        self.assertTrue(np.array_equal(data, uncompressed), "Python version is OK")
        t2 = time.perf_counter()
        compressed = _agi_bitfield.compress(data)
        t3 = time.perf_counter()
        uncompressed = agi_bitfield.decompress(compressed, data.shape)
        self.assertTrue(np.array_equal(data, uncompressed), "Cython version is OK")
        print("speed-up:", (t1 - t0) / (t3 - t2))


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestUtil))
    testsuite.addTest(loadTests(TestRow))
    testsuite.addTest(loadTests(TestCompression))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
