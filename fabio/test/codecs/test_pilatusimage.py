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
"""Pilatus Tiff Unit tests"""
from __future__ import print_function, with_statement, division, absolute_import

import unittest
import logging

logger = logging.getLogger(__name__)

import fabio
from ..utilstest import UtilsTest


class TestPilatus(unittest.TestCase):
    # filename dim1 dim2 min max mean stddev
    TESTIMAGES = [
        ("lysb_5mg-1.90s_SAXS.bz2", 487, 619, 0, 1300, 29.4260, 17.7367),
        ("lysb_5mg-1.90s_SAXS.gz", 487, 619, 0, 1300, 29.4260, 17.7367),
        ("lysb_5mg-1.90s_SAXS", 487, 619, 0, 1300, 29.4260, 17.7367),
    ]

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
            obj = fabio.pilatusimage.PilatusImage()
            obj.read(UtilsTest.getimage(name))

            self.assertAlmostEqual(mini, obj.getmin(), 2, "getmin [%s,%s]" % (mini, obj.getmin()))
            self.assertAlmostEqual(maxi, obj.getmax(), 2, "getmax [%s,%s]" % (maxi, obj.getmax()))
            self.assertAlmostEqual(mean, obj.getmean(), 2, "getmean [%s,%s]" % (mean, obj.getmean()))
            self.assertAlmostEqual(stddev, obj.getstddev(), 2, "getstddev [%s,%s]" % (stddev, obj.getstddev()))
            self.assertEqual(shape, obj.shape)

    def test_header(self):
        for params in self.TESTIMAGES:
            name = params[0]
            obj = fabio.pilatusimage.PilatusImage()
            obj.read(UtilsTest.getimage(name))

            expected_keys = [
                "Pixel_size",
                "Silicon",
                "Exposure_time",
                "Exposure_period",
                "Tau",
                "Count_cutoff",
                "Threshold_setting",
                "Gain_setting",
                "N_excluded_pixels",
                "Excluded_pixels",
                "Flat_field",
                "Trim_directory"]
            self.assertEqual(list(obj.header.keys()), expected_keys)

            expected_values = {
                "Pixel_size": "172e-6 m x 172e-6 m",
                "Silicon": "sensor, thickness 0.000320 m",
                "Exposure_time": "90.000000 s",
                "Exposure_period": "90.000000 s",
                "Tau": "0 s",
                "Count_cutoff": "1048574 counts",
                "Threshold_setting": "0 eV",
                "Gain_setting": "not implemented (vrf = 9.900)",
                "N_excluded_pixels": "0",
                "Excluded_pixels": "(nil)",
                "Flat_field": "(nil)",
                "Trim_directory": "(nil)"}

            self.assertEqual(dict(obj.header), expected_values)

    def test_frame(self):
        for params in self.TESTIMAGES:
            name = params[0]
            dim1, dim2 = params[1:3]
            obj = fabio.pilatusimage.PilatusImage()
            obj.read(UtilsTest.getimage(name))

            self.assertEqual(obj.nframes, 1)
            frame = obj.getframe(0)
            self.assertIsNotNone(frame)
            self.assertIsNotNone(frame.data)
            self.assertEqual(frame.data.shape, (dim2, dim1))
            self.assertEqual(len(frame.header), 12)


class TestPilatus1M(unittest.TestCase):
    # filename dim1 dim2 min max mean stddev
    TESTIMAGES = [
        ("Pilatus1M.tif.bz2", 981, 1043),
        ("Pilatus1M.tif", 981, 1043),
    ]

    def setUp(self):
        import fabio.utils.pilutils
        if fabio.utils.pilutils.Image is None:
            self.skipTest("No TIFF decoder available for LZW")

    def test_read(self):
        """
        Test the reading of Mar345 images
        """
        for params in self.TESTIMAGES:
            name = params[0]
            logger.debug("Processing: %s" % name)
            dim1, dim2 = params[1:3]
            shape = dim2, dim1
            obj = fabio.pilatusimage.PilatusImage()
            obj.read(UtilsTest.getimage(name))
            self.assertEqual(shape, obj.shape, "dim2")

    def test_header(self):
        for params in self.TESTIMAGES:
            name = params[0]
            obj = fabio.pilatusimage.PilatusImage()
            obj.read(UtilsTest.getimage(name))
            expected_keys = [
                "Pixel_size",
                "Silicon",
                "Exposure_time",
                "Exposure_period",
                "Tau",
                "Count_cutoff",
                "Threshold_setting",
                "Gain_setting",
                "N_excluded_pixels",
                "Excluded_pixels",
                "Flat_field",
                "Trim_file",
                "Image_path",
                "Energy_range",
                "Detector_distance",
                "Detector_Voffset",
                "Beam_xy",
                "Flux",
                "Filter_transmission",
                "Start_angle",
                "Angle_increment",
                "Detector_2theta",
                "Polarization",
                "Alpha",
                "Kappa",
                "Phi",
                "Chi",
                "Oscillation_axis",
                "N_oscillations"]
            self.assertEqual(list(obj.header.keys()), expected_keys)


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestPilatus))
    testsuite.addTest(loadTests(TestPilatus1M))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
