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
Test JPEG format
"""

import unittest
import os
import shutil
import logging

logger = logging.getLogger(__name__)

import fabio
from ... import jpegimage
from ..utilstest import UtilsTest

TEST_DIRECTORY = None
# Temporary directory where storing test data


def setUpModule():
    global TEST_DIRECTORY
    TEST_DIRECTORY = os.path.join(UtilsTest.tempdir, __name__)
    os.makedirs(TEST_DIRECTORY)


def tearDownModule():
    shutil.rmtree(TEST_DIRECTORY)


class TestJpegImage(unittest.TestCase):
    """Test the class format"""

    def setUp(self):
        if jpegimage.Image is None:
            self.skipTest("PIL is not available")

    def test_read_uint8(self):
        filename = UtilsTest.getimage("rand_uint8.jpg.bz2")[:-4]
        image_format = jpegimage.JpegImage()
        image = image_format.read(filename)
        self.assertEqual(image.data.shape, (64, 64))
        self.assertIn("jfif", image.header)

    def test_read_failing_file(self):
        filename = os.path.join(TEST_DIRECTORY, "2.jpg")
        filename_source = UtilsTest.getimage("rand_uint8.jpg.bz2")[:-4]

        with open(filename_source, "r+b") as fsource:
            with open(filename, "w+b") as ftest:
                ftest.write(fsource.read())
                ftest.seek(1)
                ftest.write(b".")

        image_format = jpegimage.JpegImage()
        try:
            _image = image_format.read(filename)
            self.fail()
        except IOError:
            pass

    def test_read_empty_file(self):
        filename = os.path.join(TEST_DIRECTORY, "3.jpg")
        f = open(filename, "wb")
        f.close()

        image_format = jpegimage.JpegImage()
        try:
            _image = image_format.read(filename)
            self.fail()
        except IOError:
            pass

    def test_read_missing_file(self):
        filename = os.path.join(TEST_DIRECTORY, "4.jpg")

        image_format = jpegimage.JpegImage()
        try:
            _image = image_format.read(filename)
            self.fail()
        except IOError:
            pass


class TestPilNotAvailable(unittest.TestCase):

    def setUp(self):
        filename = UtilsTest.getimage("rand_uint8.jpg.bz2")[:-4]
        self.filename = filename

        self.old = jpegimage.Image

    def tearDown(self):
        jpegimage.Image = self.old
        self.filename = None
        self.data = None

    def open_image(self):
        return fabio.open(self.filename)

    def test_with_pil(self):
        if jpegimage.Image is None:
            self.skipTest("PIL is not available")
        image = self.open_image()
        self.assertIsInstance(image, jpegimage.JpegImage)
        self.assertEqual(image.data.shape, (64, 64))
        self.assertIn("jfif", image.header)

    def test_without_pil(self):
        try:
            old = jpegimage.Image
            jpegimage.Image = None
            try:
                _image = self.open_image()
                self.fail()
            except IOError:
                pass
        finally:
            jpegimage.Image = old


class TestJpegImageInsideFabio(unittest.TestCase):
    """Test the format inside the fabio framework"""

    def test_read_uint8(self):
        if jpegimage.Image is None:
            self.skipTest("PIL is not available")
        filename = UtilsTest.getimage("rand_uint8.jpg.bz2")[:-4]
        image = fabio.open(filename)
        self.assertIsInstance(image, jpegimage.JpegImage)
        self.assertEqual(image.data.shape, (64, 64))
        self.assertIn("jfif", image.header)


def suite():
    loader = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loader(TestJpegImage))
    testsuite.addTest(loader(TestJpegImageInsideFabio))
    testsuite.addTest(loader(TestPilNotAvailable))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
