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
"""Tiff Unit tests"""

from __future__ import print_function, with_statement, division, absolute_import
import unittest
import os
import logging

logger = logging.getLogger(__name__)

import fabio
from fabio import tifimage
from ..utilstest import UtilsTest


class TestTif(unittest.TestCase):
    # filename dim1 dim2 min max mean stddev
    TESTIMAGES = [
        ("Feb09-bright-00.300s_WAXS.bz2", 1042, 1042, 0, 65535, 8546.6414, 1500.4198),
        ("Feb09-bright-00.300s_WAXS.gz", 1042, 1042, 0, 65535, 8546.6414, 1500.4198),
        ("Feb09-bright-00.300s_WAXS", 1042, 1042, 0, 65535, 8546.6414, 1500.4198)]

    def test_read(self):
        """
        Test the reading of Mar345 images
        """
        for params in self.TESTIMAGES:
            name = params[0]
            logger.debug("Processing: %s" % name)
            dim1, dim2 = params[1:3]
            shape = dim2, dim1
            mini, maxi, mean, stddev = params[3:]
            obj = fabio.tifimage.TifImage()
            obj.read(UtilsTest.getimage(name))

            self.assertAlmostEqual(mini, obj.getmin(), 2, "getmin [%s,%s]" % (mini, obj.getmin()))
            self.assertAlmostEqual(maxi, obj.getmax(), 2, "getmax [%s,%s]" % (maxi, obj.getmax()))
            self.assertAlmostEqual(mean, obj.getmean(), 2, "getmean [%s,%s]" % (mean, obj.getmean()))
            self.assertAlmostEqual(stddev, obj.getstddev(), 2, "getstddev [%s,%s]" % (stddev, obj.getstddev()))
            self.assertEqual(shape, obj.shape, "dim1")

    def test_header(self):
        for params in self.TESTIMAGES:
            name = params[0]
            logger.debug("Processing: %s" % name)
            obj = fabio.tifimage.TifImage()
            obj.read(UtilsTest.getimage(name))

            # The key order is not the same depending on Python2 or 3
            expected_keys = set([
                'info',
                'photometricInterpretation',
                'rowsPerStrip',
                'nColumns',
                'compression',
                'sampleFormat',
                'imageDescription',
                'nRows',
                'colormap',
                'nBits',
                'date',
                'software',
                'compression_type',
                'stripOffsets',
                'stripByteCounts'])
            self.assertEqual(set(obj.header.keys()), expected_keys)

    def test_frame(self):
        for params in self.TESTIMAGES:
            name = params[0]
            logger.debug("Processing: %s" % name)
            dim1, dim2 = params[1:3]
            obj = fabio.tifimage.TifImage()
            obj.read(UtilsTest.getimage(name))

            self.assertEqual(obj.nframes, 1)
            frame = obj.getframe(0)
            self.assertIsNotNone(frame)
            self.assertIsNotNone(frame.data)
            self.assertEqual(frame.data.shape, (dim2, dim1))
            self.assertEqual(len(frame.header.keys()), 15)


class TestTifImage_Pilatus(unittest.TestCase):
    def setUp(self):
        self.fn = {}
        for i in ["pilatus2M.tif", "pilatus2M.edf"]:
            self.fn[i] = UtilsTest.getimage(i + ".bz2")
        for i in self.fn:
            assert os.path.exists(self.fn[i])

    def test1(self):
        """
        Testing pilatus tif bug
        """
        o1 = fabio.open(self.fn["pilatus2M.tif"]).data
        o2 = fabio.open(self.fn["pilatus2M.edf"]).data
        self.assertEqual(abs(o1 - o2).max(), 0.0)


class TestTifImage_Packbits(unittest.TestCase):
    def setUp(self):
        self.fn = {}
        for i in ["oPPA_5grains_0001.tif", "oPPA_5grains_0001.edf"]:
            self.fn[i] = UtilsTest.getimage(i + ".bz2")
        for i in self.fn:
            assert os.path.exists(self.fn[i])

    def test1(self):
        """
        Testing packbit comressed data tif bug
        """
        o1 = fabio.open(self.fn["oPPA_5grains_0001.tif"]).data
        o2 = fabio.open(self.fn["oPPA_5grains_0001.edf"]).data
        self.assertEqual(abs(o1 - o2).max(), 0.0)


class TestTifImage_fit2d(unittest.TestCase):
    def setUp(self):
        self.fn = {}
        for i in ["fit2d.tif", "fit2d.edf"]:
            self.fn[i] = UtilsTest.getimage(i + ".bz2")
        for i in self.fn:
            assert os.path.exists(self.fn[i])

    def test1(self):
        """
        Testing packbit comressed data tif bug
        """
        o1 = fabio.open(self.fn["fit2d.tif"]).data
        o2 = fabio.open(self.fn["fit2d.edf"]).data
        self.assertEqual(abs(o1 - o2).max(), 0.0)


class TestTifImage_A0009(unittest.TestCase):
    """
    test image from ??? with this error
a0009.tif TIFF 1024x1024 1024x1024+0+0 16-bit Grayscale DirectClass 2MiB 0.000u 0:00.010
identify: a0009.tif: invalid TIFF directory; tags are not sorted in ascending order. `TIFFReadDirectory' @ tiff.c/TIFFWarnings/703.
identify: a0009.tif: TIFF directory is missing required "StripByteCounts" field, calculating from imagelength. `TIFFReadDirectory' @ tiff.c/TIFFWarnings/703.

    """
    def setUp(self):
        self.fn = {}
        for i in ["a0009.tif", "a0009.edf"]:
            self.fn[i] = UtilsTest.getimage(i + ".bz2")[:-4]
        for i in self.fn:
            assert os.path.exists(self.fn[i])

    def test1(self):
        """
        Testing packbit comressed data tif bug
        """
        o1 = fabio.open(self.fn["a0009.tif"]).data
        o2 = fabio.open(self.fn["a0009.edf"]).data
        self.assertEqual(abs(o1 - o2).max(), 0.0)


class TestGzipTif(unittest.TestCase):
    def setUp(self):
        self.unzipped = UtilsTest.getimage("oPPA_5grains_0001.tif.bz2")[:-4]
        self.zipped = self.unzipped + ".gz"
        assert os.path.exists(self.zipped)
        assert os.path.exists(self.unzipped)

    def test1(self):
        o1 = fabio.open(self.zipped)
        o2 = fabio.open(self.unzipped)
        self.assertEqual(o1.data[0, 0], 10)
        self.assertEqual(o2.data[0, 0], 10)


class TestTif_Rect(unittest.TestCase):
    def setUp(self):
        self.fn = UtilsTest.getimage("testmap1_0002.tif.bz2")[:-4]

    def test1(self):
        for ext in ["", ".gz", ".bz2"]:
            o1 = fabio.open(self.fn + ext)
            self.assertEqual(o1.data.shape, (100, 120))


class TestTif_Colormap(unittest.TestCase):
    def setUp(self):
        self.fn = UtilsTest.getimage("indexed_color.tif.bz2")[:-4]

    def tearDown(self):
        tifimage._USE_PIL = True
        tifimage._USE_TIFFIO = True

    def _test_base(self):
        for ext in ["", ".gz", ".bz2"]:
            image = fabio.open(self.fn + ext)
            self.assertEqual(image.data.shape, (16, 16, 3))
            self.assertEqual(image.data[0, 0].tolist(), [255, 0, 0])
            self.assertEqual(image.data[8, 8].tolist(), [0, 252, 255])
            self.assertEqual(image.data[15, 15].tolist(), [255, 96, 0])

    def test_pil(self):
        if tifimage.PIL is None:
            self.skipTest("PIL is not available")
        tifimage._USE_TIFFIO = False
        self._test_base()

    def test_tiffio(self):
        tifimage._USE_PIL = False
        self._test_base()


class TestTif_LibTiffPic(unittest.TestCase):
    """Test TIFF loading from libtiffpic dataset"""

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.files = UtilsTest.resources.getdir("libtiffpic.tar.gz")

    def test_all_images(self):
        if tifimage.PIL is None:
            self.skipTest("PIL is not available")
        for filename in self.files:
            if filename.endswith(".tif"):
                with fabio.open(filename):
                    pass


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestTif))
    testsuite.addTest(loadTests(TestGzipTif))
    testsuite.addTest(loadTests(TestTif_Rect))
    testsuite.addTest(loadTests(TestTifImage_A0009))
    testsuite.addTest(loadTests(TestTifImage_fit2d))
    testsuite.addTest(loadTests(TestTifImage_Packbits))
    testsuite.addTest(loadTests(TestTifImage_Pilatus))
    testsuite.addTest(loadTests(TestTif_Colormap))
    testsuite.addTest(loadTests(TestTif_LibTiffPic))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
