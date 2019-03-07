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
Test JPEG 2000 format
"""

from __future__ import print_function, with_statement, division, absolute_import

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
    if jpeg2kimage.PIL is None:
        return False
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
        return False
    import glymur
    if glymur.version.openjpeg_version_tuple < [1, 5, 0]:
        return False
    return True


class TestJpeg2KImage(unittest.TestCase):
    """Test the class format"""

    def setUp(self):
        if not isPilUsable() and not isGlymurUsable():
            self.skipTest("PIL nor glymur are available")

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
        if not isPilUsable() and not isGlymurUsable():
            self.skipTest("PIL is not available")

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
            self.skipTest("glymur is not available")

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
