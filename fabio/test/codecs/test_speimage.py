#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Project: X-ray image reader
#             https://github.com/silx-kit/fabio
#
#    Copyright (C) 2016 Univeristy Köln, Germany
#
#    Principal author:       Clemens Prescher (c.prescher@uni-koeln.de)
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

__authors__ = ["Clemens Prescher"]
__contact__ = "c.prescher@uni-koeln.de"
__license__ = "MIT"
__copyright__ = "Clemens Prescher/Univeristy Köln, Germany"
__date__ = "03/04/2020"

import unittest
import numpy
import logging

logger = logging.getLogger(__name__)

import fabio
from fabio.speimage import SpeImage
from ..utilstest import UtilsTest


class TestSpeImage(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestSpeImage, cls).setUpClass()
        cls.v2_spe_filename = UtilsTest.getimage('v2.SPE.bz2')[:-4]
        cls.v2_converted_spe_filename = UtilsTest.getimage('v2_converted.SPE.bz2')[:-4]
        cls.v3_spe_filename = UtilsTest.getimage('v3.spe.bz2')[:-4]
        cls.v3_custom_roi_filename = UtilsTest.getimage('v3_custom_roi.spe.bz2')[:-4]
        cls.v3_2frames_filename = UtilsTest.getimage('v3_2frames.spe.bz2')[:-4]

    @classmethod
    def tearDownClass(cls):
        super(TestSpeImage, cls).tearDownClass()

    def setUp(self):
        self.v2_spe_file = SpeImage()
        self.v2_spe_file.read(self.v2_spe_filename)

        self.v3_spe_file = SpeImage()
        self.v3_spe_file.read(self.v3_spe_filename)

        self.v2_converted_spe_file = SpeImage()
        self.v2_converted_spe_file.read(self.v2_converted_spe_filename)

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        # free the associated memory
        self.v2_spe_file = self.v3_spe_file = self.v2_converted_spe_file = None

    def test_reading_version2_spe(self):
        self.assertEqual(self.v2_spe_file.header['version'], 2)
        self.assertEqual(self.v3_spe_file.header['version'], 3)
        self.assertEqual(self.v2_converted_spe_file.header['version'], 3)

    def test_calibration(self):
        self.assertGreater(len(self.v2_spe_file.header['x_calibration']), 0)
        self.assertGreater(len(self.v3_spe_file.header['x_calibration']), 0)
        self.assertGreater(len(self.v2_converted_spe_file.header['x_calibration']), 0)

    #
    def test_time(self):
        self.assertEqual(self.v2_spe_file.header['time'], "07/13/2013 19:42:23")
        self.assertEqual(self.v3_spe_file.header['time'], "09/06/2013 16:50:39.445678")
        self.assertEqual(self.v2_converted_spe_file.header['time'], "05/10/2013 10:34:27")

    def test_exposure_time(self):
        self.assertEqual(self.v2_spe_file.header['exposure_time'], 0.5)
        self.assertEqual(self.v3_spe_file.header['exposure_time'], 0.1)
        self.assertEqual(self.v2_converted_spe_file.header['exposure_time'], 0.18)

    def test_detector(self):
        self.assertEqual(self.v2_spe_file.header['detector'], 'unspecified')
        self.assertEqual(self.v3_spe_file.header['detector'], "PIXIS: 100BR")
        self.assertEqual(self.v2_converted_spe_file.header['detector'], 'unspecified')

    def test_grating(self):
        self.assertEqual(self.v2_spe_file.header['grating'], '300.0')
        self.assertEqual(self.v3_spe_file.header['grating'], '860nm 300')
        self.assertEqual(self.v2_converted_spe_file.header['grating'], '300.0')

    def test_center_wavelength(self):
        self.assertEqual(self.v2_spe_file.header['center_wavelength'], 750)
        self.assertEqual(self.v3_spe_file.header['center_wavelength'], 500)
        self.assertEqual(self.v2_converted_spe_file.header['center_wavelength'], 750)

    def test_roi(self):
        self.assertEqual(self.v3_spe_file.header['roi'], (0, 1024, 0, 100))
        self.v3_custom_region = SpeImage()
        self.v3_custom_region.read(self.v3_custom_roi_filename)
        self.assertEqual(self.v3_custom_region.header['roi'], (100, 600, 10, 60))
        self.assertEqual(len(self.v3_custom_region.header['x_calibration']),
                         self.v3_custom_region.header['x_dim'])

    def test_read_data(self):
        self.assertEqual(self.v2_spe_file.data.shape, (100, 1340))
        self.assertEqual(self.v3_spe_file.data.shape, (100, 1024))
        self.assertEqual(self.v2_converted_spe_file.data.shape, (100, 1340))

    def test_multiple_frames(self):
        self.v3_2frames_file = SpeImage()
        self.v3_2frames_file.read(self.v3_2frames_filename)
        self.assertEqual(self.v3_2frames_file.data.shape, (255, 1024))
        frame1 = self.v3_2frames_file.data

        self.v3_2frames_file.read(self.v3_2frames_filename, 1)
        frame2 = self.v3_2frames_file.data

        self.assertFalse(numpy.array_equal(frame1, frame2))
        self.assertEqual(frame1.shape, frame2.shape)

    def test_fabio_integration(self):
        v2_file = fabio.open(self.v2_spe_filename)
        v3_file = fabio.open(self.v3_spe_filename)
        v2_file_gz = fabio.open(self.v2_spe_filename + ".gz")
        v3_file_gz = fabio.open(self.v3_spe_filename + ".gz")
        v2_file_bz = fabio.open(self.v2_spe_filename + ".bz2")
        v3_file_bz = fabio.open(self.v3_spe_filename + ".bz2")
        self.assertEqual(abs(v2_file.data - v2_file_gz.data).max(), 0, "v2/gz")
        self.assertEqual(abs(v3_file.data - v3_file_gz.data).max(), 0, "v3/gz")
        self.assertEqual(abs(v2_file.data - v2_file_bz.data).max(), 0, "v2/bz")
        self.assertEqual(abs(v3_file.data - v3_file_bz.data).max(), 0, "v3/bz")


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestSpeImage))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
