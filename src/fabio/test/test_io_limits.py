#!/usr/bin/env python

"""
Test IO size limits
"""

import os
import unittest
import logging
import numpy
import tempfile
import shutil

logger = logging.getLogger(__name__)

import fabio.edfimage
import fabio.tifimage


class _CommonIOLimitTest(unittest.TestCase):
    IMAGETYPE = None
    HEADERSIZE = 0

    @classmethod
    def setUpClass(cls):
        cls.test_dir = tempfile.mkdtemp()
        cls.test_filename = os.path.join(cls.test_dir, "data")

        # A single IO operation is limited to `nbytes_single_io` bytes
        nbytes_single_io = 2 ** 31
        cls.data_dtype = numpy.uint32
        itemsize = 4

        # Make sure we will need more than one IO operation
        n = int((nbytes_single_io / itemsize) ** 0.5) + 1
        cls.data_shape = n, n
        cls.data_size = n * n
        cls.data_size_bytes = n * n * itemsize
        cls.save_data()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_dir)

    @classmethod
    def generate_data(cls):
        return (
            numpy.arange(cls.data_size).reshape(cls.data_shape).astype(cls.data_dtype)
        )

    @classmethod
    def save_data(cls):
        if cls.IMAGETYPE is None:
            raise unittest.SkipTest("no image type specified")
        if logger.getEffectiveLevel() > logging.DEBUG:
            raise unittest.SkipTest("test requires debug level logging")
        cls.IMAGETYPE(data=cls.generate_data()).write(cls.test_filename)

    @classmethod
    def filesize(cls):
        return os.stat(cls.test_filename).st_size

    def test_filesize(self):
        expected = self.data_size_bytes + self.HEADERSIZE
        self.assertEqual(self.filesize(), expected)

    def test_io_roundtrip(self):
        image = self.IMAGETYPE()
        data = image.read(self.test_filename).data
        self.assertEqual(self.data_shape, data.shape)
        self.assertEqual(self.data_dtype, data.dtype)
        self.assertEqual(data[0, 0], 0)
        self.assertEqual(data[-1, -1], self.data_size - 1)


class TestEdf(_CommonIOLimitTest):
    IMAGETYPE = fabio.edfimage.edfimage
    HEADERSIZE = 512


class TestTiff(_CommonIOLimitTest):
    IMAGETYPE = fabio.tifimage.tifimage
    HEADERSIZE = 196


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestEdf))
    testsuite.addTest(loadTests(TestTiff))
    return testsuite


if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite())
