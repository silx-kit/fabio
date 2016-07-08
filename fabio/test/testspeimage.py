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
# Get ready for python3:
from __future__ import with_statement, print_function, division

__authors__ = ["Clemens Prescher"]
__contact__ = "c.prescher@uni-koeln.de"
__license__ = "MIT"
__copyright__ = "Clemens Prescher"
__date__ = "07/07/2016"

import unittest
import os
import sys

import numpy as np


fabio = sys.modules["fabio"]
from fabio.speimage import SpeImage
from .utilstest import UtilsTest

v2_spe_filename = os.path.join(UtilsTest.image_home, 'v2.SPE')
v2_converted_spe_file = os.path.join(UtilsTest.image_home, 'v2_converted.SPE')
v3_spe_filename = os.path.join(UtilsTest.image_home, 'v3.spe')
v3_custom_roi_filename = os.path.join(UtilsTest.image_home, 'v3_custom_roi.spe')
v3_2frames_filename = os.path.join(UtilsTest.image_home, 'v3_2frames.spe')


class TestSpeImage(unittest.TestCase):
    def setUp(self):
        self.v2_spe_file = SpeImage()
        self.v2_spe_file.read(v2_spe_filename)

        self.v3_spe_file = SpeImage()
        self.v3_spe_file.read(v3_spe_filename)

        self.v2_converted_spe_file = SpeImage()
        self.v2_converted_spe_file.read(v2_converted_spe_file)

    def test_reading_version2_spe(self):
        self.assertEqual(self.v2_spe_file.header['version'], 2)
        # self.assertEqual(self.v3_spe_file.header['version'], 3)
        # self.assertEqual(self.v2_converted_spe_file.header['version'], 3)

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
        self.v3_custom_region.read(v3_custom_roi_filename)
        self.assertEqual(self.v3_custom_region.header['roi'], (100, 600, 10, 60))
        self.assertEqual(len(self.v3_custom_region.header['x_calibration']),
                         self.v3_custom_region.header['x_dim'])

    def test_read_data(self):
        self.assertEqual(self.v2_spe_file.data.shape, (100, 1340))
        self.assertEqual(self.v3_spe_file.data.shape, (100, 1024))
        self.assertEqual(self.v2_converted_spe_file.data.shape, (100, 1340))

    def test_multiple_frames(self):
        self.v3_2frames_file = SpeImage()
        self.v3_2frames_file.read(v3_2frames_filename)
        self.assertEqual(self.v3_2frames_file.data.shape, (255, 1024))
        frame1 = self.v3_2frames_file.data

        self.v3_2frames_file.read(v3_2frames_filename, 1)
        frame2 = self.v3_2frames_file.data

        self.assertFalse(np.array_equal(frame1, frame2))
        self.assertEqual(frame1.shape, frame2.shape)
