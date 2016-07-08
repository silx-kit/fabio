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
import datetime
import os

from fabio.spe import SpeImage as SpeImage

image_folder = os.path.join(os.path.dirname(__file__), '../../testimages')

v2_spe_filename = os.path.join(image_folder, 'v2.SPE')
v2_converted_spe_file = os.path.join(image_folder, 'converted_v2.SPE')
v3_spe_file = os.path.join(image_folder, 'v3.spe')

class TestSpeImage(unittest.TestCase):
    def setUp(self):
        self.v2_spe_file = SpeImage()
        self.v2_spe_file.read(v2_spe_filename)

        self.v3_spe_file = SpeImage()
        self.v3_spe_file.read(v3_spe_file)

        self.v2_converted_spe_file = SpeImage()
        self.v2_converted_spe_file.read(v2_converted_spe_file)

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
        self.assertEqual(self.v2_spe_file.date_time, datetime.datetime(2013, 7, 13, 19, 42, 23))
        self.assertEqual(self.v3_spe_file.date_time, datetime.datetime(2013, 9, 6, 16, 50, 39, 445678,
                                                                       self.v3_spe_file.date_time.tzinfo))
        self.assertEqual(self.v2_converted_spe_file.date_time,
                         datetime.datetime(2013, 5, 10, 10, 34, 27, 0,
                                           self.v2_converted_spe_file.date_time.tzinfo))

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
        self.assertEqual(self.v3_spe_file.roi_modus, 'CustomRegions')
        self.assertEqual(self.v3_spe_file.get_roi(), [0, 1023, 0, 99])

        self.vers3_spe_file_custom_region = SpeFile(os.path.join(unittest_folder, 'SPE_v3_CustomRegions.spe'))
        self.assertEqual(self.vers3_spe_file_custom_region.roi_modus, 'CustomRegions')
        self.assertEqual(self.vers3_spe_file_custom_region.get_roi(), [100, 599, 10, 59])
        self.assertEqual(len(self.vers3_spe_file_custom_region.x_calibration),
                         self.vers3_spe_file_custom_region.get_dimension()[0])

        self.vers3_spe_file_full_sensor = SpeFile(os.path.join(unittest_folder, 'SPE_v3_FullSensor.spe'))
        self.assertEqual(self.vers3_spe_file_full_sensor.roi_modus, 'FullSensor')
        dimensions = self.vers3_spe_file_full_sensor.get_dimension()
        self.assertEqual(self.vers3_spe_file_full_sensor.get_roi(),
                         [0, dimensions[0] - 1, 0, dimensions[1] - 1])
    #
    # def test_multiple_frames(self):
    #     self.spe3_2frames_file = SpeFile(os.path.join(unittest_folder, 'SPE_v3_PIMAX_2frames.spe'))
