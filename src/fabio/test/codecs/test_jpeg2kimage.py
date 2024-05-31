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
Test JPEG 2000 format
"""

import unittest
import numpy
import logging
try:
    from PIL import Image
except ImportError:
    Image = None

logger = logging.getLogger(__name__)

import fabio
from ... import jpeg2kimage
from ..utilstest import UtilsTest


def isPilUsable():
    print("jpeg2kimage.PIL:", jpeg2kimage.PIL)
    if jpeg2kimage.PIL is None:
        return None
    try:
        if hasattr(jpeg2kimage.PIL.Image, "frombytes"):
            frombytes = jpeg2kimage.PIL.Image.frombytes
        else:
            frombytes = jpeg2kimage.PIL.Image.frombuffer
        frombytes("1", (2, 2), b"", decoder_name='jpeg2k')
    except Exception as e:
        if e.args[0] == "decoder jpeg2k not available":
            return False
        # Skip decoding error
    return True


def isGlymurUsable():
    if jpeg2kimage.glymur is None:
        return None
    import glymur
    if tuple(glymur.version.openjpeg_version_tuple) < (1, 5, 0):
        return False
    return True


class TestJpeg2KImage(unittest.TestCase):
    """Test the class format"""

    def setUp(self):
        if not (isPilUsable() or isGlymurUsable()):
            self.skipTest("nor PIL neither glymur are available")

    def loadImage(self, filename):
        image_format = jpeg2kimage.Jpeg2KImage()
        image = image_format.read(filename)
        return image

    def test_open_uint8(self):
        filename = "binned_data_uint8.jp2"
        filename = UtilsTest.getimage(filename + ".bz2")[:-4]
        image = self.loadImage(filename)
        self.assertEqual(image.data.shape, (120, 120))
        self.assertEqual(image.data.dtype, numpy.uint8)

    def test_open_uint16(self):
        filename = "binned_data_uint16.jp2"
        filename = UtilsTest.getimage(filename + ".bz2")[:-4]
        image_format = jpeg2kimage.Jpeg2KImage()
        image = image_format.read(filename)
        self.assertEqual(image.data.shape, (120, 120))
        self.assertEqual(image.data.dtype, numpy.uint16)

    def test_open_wrong_format(self):
        filename = "MultiFrame.edf"
        filename = UtilsTest.getimage(filename + ".bz2")[:-4]
        image_format = jpeg2kimage.Jpeg2KImage()
        try:
            _image = image_format.read(filename)
            self.fail()
        except IOError:
            pass

    def test_open_missing_file(self):
        filename = "___missing_file___.___"
        image_format = jpeg2kimage.Jpeg2KImage()
        try:
            _image = image_format.read(filename)
            self.fail()
        except IOError:
            pass


class TestJpeg2KImage_PIL(TestJpeg2KImage):
    """Test the class format using a specific decoder"""

    def setUp(self):
        if not isPilUsable():
            self.skipTest("PIL is not available or has no support for JPEG2000")

    @classmethod
    def setUpClass(cls):
        # Remove other decoders
        cls.old = jpeg2kimage.glymur
        jpeg2kimage.glymur = None

    @classmethod
    def tearDownClass(cls):
        # Remove other decoders
        jpeg2kimage.glymur = cls.old
        cls.old = None


class TestJpeg2KImage_glymur(TestJpeg2KImage):
    """Test the class format using a specific decoder"""

    def setUp(self):
        if not isGlymurUsable():
            self.skipTest("glymur is not available or too old")

    @classmethod
    def setUpClass(cls):
        # Remove other decoders
        cls.old = jpeg2kimage.PIL
        jpeg2kimage.PIL = None

    @classmethod
    def tearDownClass(cls):
        # Remove other decoders
        jpeg2kimage.PIL = cls.old
        cls.old = None


class TestJpeg2KImage_fabio(TestJpeg2KImage):
    """Test the format inside the fabio framework"""

    def loadImage(self, filename):
        """Use the fabio API instead of using the image format"""
        image = fabio.open(filename)
        return image


def suite():
    loader = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loader(TestJpeg2KImage))
    testsuite.addTest(loader(TestJpeg2KImage_PIL))
    testsuite.addTest(loader(TestJpeg2KImage_glymur))
    testsuite.addTest(loader(TestJpeg2KImage_fabio))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
