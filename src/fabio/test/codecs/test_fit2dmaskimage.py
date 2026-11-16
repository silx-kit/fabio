#!/usr/bin/env python
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
"""Test the fit2d mask reader

Updated by Jerome Kieffer (jerome.kieffer@esrf.eu), 2011
28/11/2014
"""

import bz2
import gzip
import io
import logging
import os
import struct
import tempfile
import unittest

import numpy

import fabio
from fabio.fit2dmaskimage import fit2dmaskimage

from ..utilstest import UtilsTest

logger = logging.getLogger(__name__)


class TestFaceMask(unittest.TestCase):
    """test the picture of a face"""

    def setUp(self):
        """
        download images
        """
        self.filename = UtilsTest.getimage("face.msk.bz2")[:-4]
        self.edffilename = UtilsTest.getimage("face.edf.bz2")[:-4]

    def test_getmatch(self):
        """test edf and msk are the same"""
        i = fit2dmaskimage()
        i.read(self.filename)
        j = fabio.open(self.edffilename)
        self.assertEqual(i.shape, j.shape)
        self.assertEqual(i.data.shape, j.data.shape)
        diff = j.data - i.data
        sumd = abs(diff).sum(dtype=float)
        self.assertEqual(sumd, 0.0)


class TestClickedMask(unittest.TestCase):
    """A few random clicks to make a test mask"""

    def setUp(self):
        """
        download images
        """
        self.filename = UtilsTest.getimage("fit2d_click.msk.bz2")[:-4]
        self.edffilename = UtilsTest.getimage("fit2d_click.edf.bz2")[:-4]

    def test_read(self):
        """Check it reads a mask OK"""
        i = fit2dmaskimage()
        i.read(self.filename)
        self.assertEqual(i.shape, (1024, 1024))
        self.assertEqual(i.bpp, 1)
        self.assertEqual(i.bytecode, numpy.uint8)
        self.assertEqual(i.data.shape, (1024, 1024))

    def test_getmatch(self):
        """test edf and msk are the same"""
        i = fit2dmaskimage()
        j = fabio.open(self.edffilename)
        i.read(self.filename)
        self.assertEqual(i.data.shape, j.data.shape)
        diff = j.data - i.data
        self.assertEqual(i.getmax(), 1)
        self.assertEqual(i.getmin(), 0)
        sumd = abs(diff).sum(dtype=float)
        self.assertEqual(sumd, 0)


class TestMskWrite(unittest.TestCase):
    """
    Write dummy mask files with various compression schemes

    """

    def setUp(self):
        shape = (199, 211)  # those are prime numbers
        self.data = numpy.random.random(shape) > 0.6
        self.header = fit2dmaskimage.check_header()

    def atest(self):
        e = fit2dmaskimage(data=self.data, header=self.header)
        e.write(self.filename)
        r = fabio.open(self.filename)
        self.assertEqual(e.shape, r.shape, "shape are the same")
        if r.header != self.header:
            print("Issue with header in TestMskWrite.testFlat")
            for k, v in r.header.items():
                print(k, v, self.header.get(k))
            print(e.header)
            print(r.header)
            print(self.header)

        else:
            self.assertTrue(r.header == self.header, "header are OK")
        self.assertTrue(abs(r.data - self.data).max() == 0, "data are OK")

    def testFlat(self):
        self.filename = os.path.join(UtilsTest.tempdir, "random.msk")
        self.atest()

    def testGzip(self):
        self.filename = os.path.join(UtilsTest.tempdir, "random.msk.gz")
        self.atest()

    def testBzip2(self):
        self.filename = os.path.join(UtilsTest.tempdir, "random.msk.gz")
        self.atest()

    def tearDown(self):
        if os.path.isfile(self.filename):
            os.unlink(self.filename)


class TestMaskPacking(unittest.TestCase):
    """Check Fit2D bit order and row padding independently of round trips (#216)."""

    def setUp(self):
        directory = tempfile.TemporaryDirectory(dir=UtilsTest.tempdir)
        self.addCleanup(directory.cleanup)
        self.directory = directory.name

    @staticmethod
    def mask_bytes(width, height, payload):
        header = bytearray(1024)
        struct.pack_into("<7I", header, 0, 77, 65, 83, 75, width, height, 1)
        return bytes(header) + payload

    def test_read_padded_rows(self):
        # Padding bits are deliberately set: only the first nine bits count.
        raw = self.mask_bytes(9, 2, bytes([0x81, 0xFE, 0xFF, 0xFF,
                                        0x42, 0xFF, 0xFF, 0xFF]))
        image = fabio.open(io.BytesIO(raw))
        numpy.testing.assert_array_equal(image.data, [
            [1, 0, 0, 0, 0, 0, 0, 1, 0],
            [0, 1, 0, 0, 0, 0, 1, 0, 1],
        ])
        self.assertEqual(image.data.dtype, numpy.uint8)
        self.assertTrue(image.data.flags.c_contiguous)

    def test_read_all_byte_values(self):
        payload = bytes(range(256))
        expected = numpy.array([
            (value >> bit) & 1 for value in payload for bit in range(8)
        ], dtype=numpy.uint8).reshape(8, 256)
        image = fabio.open(io.BytesIO(self.mask_bytes(256, 8, payload)))
        numpy.testing.assert_array_equal(image.data, expected)

    def test_write_padded_rows(self):
        for width in (1, 7, 8, 9, 31, 32, 33, 63, 64, 65):
            with self.subTest(width=width):
                # Nonbinary, nonnative-endian, strided values must retain the
                # existing zero/nonzero mask convention.
                data = (numpy.arange(width * 6).reshape(width, 6) % 5 - 2)
                data = data.astype(">i2")[:, ::2].T[:, ::-1]
                stride = ((width + 31) // 32) * 4
                payload = bytearray(data.shape[0] * stride)
                for row, values in enumerate(data):
                    for column, value in enumerate(values):
                        if value != 0:
                            payload[row * stride + column // 8] |= 1 << (column % 8)
                filename = os.path.join(self.directory, "packed.msk")
                image = fit2dmaskimage()
                image.data = data
                image.write(filename)
                with open(filename, "rb") as stream:
                    self.assertEqual(stream.read(), self.mask_bytes(width, 3, payload))
                numpy.testing.assert_array_equal(fabio.open(filename).data, data != 0)

    def test_compressed_masks(self):
        data = numpy.ones((2, 33), dtype=numpy.uint8)
        expected = self.mask_bytes(33, 2, b"\xff\xff\xff\xff\x01\x00\x00\x00" * 2)
        for suffix, opener in ((".gz", gzip.open), (".bz2", bz2.open)):
            with self.subTest(suffix=suffix):
                filename = os.path.join(self.directory, "packed.msk" + suffix)
                fit2dmaskimage(data=data).write(filename)
                with opener(filename, "rb") as stream:
                    self.assertEqual(stream.read(), expected)
                numpy.testing.assert_array_equal(fabio.open(filename).data, data)


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestFaceMask))
    testsuite.addTest(loadTests(TestClickedMask))
    testsuite.addTest(loadTests(TestMskWrite))
    testsuite.addTest(loadTests(TestMaskPacking))
    return testsuite


if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite())
