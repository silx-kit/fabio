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

from __future__ import print_function, with_statement, division, absolute_import

"""
Test frame concept of FabioImage

"""

import unittest
import logging
import numpy

logger = logging.getLogger(__name__)

import fabio.fabioimage
import fabio.edfimage
from .utilstest import UtilsTest


class TestFrames(unittest.TestCase):

    def test_single_frame_iterator(self):
        data = numpy.array([[1, 2], [3, 4]], dtype=numpy.uint16)
        image = fabio.fabioimage.FabioImage(data=data)
        for i, frame in enumerate(image.frames()):
            if i == 0:
                self.assertIsInstance(frame, fabio.fabioimage.FabioFrame)
                self.assertIs(frame.file_container, image)
                self.assertEqual(frame.file_index, 0)
                self.assertEqual(frame.shape, data.shape)
                self.assertEqual(frame.dtype, data.dtype)
                self.assertTrue(numpy.array_equal(frame.data, data))
            else:
                self.fail()

    def test_virtual_edf_frames(self):
        header1 = {"foo": "bar"}
        data1 = numpy.array([[1, 2], [3, 4]], dtype=numpy.uint16)
        header2 = {"foo": "bar2"}
        data2 = numpy.array([[1, 2], [3, 4]], dtype=numpy.uint16)
        image = fabio.edfimage.EdfImage(data=data1, header=header1)
        image.appendFrame(data=data2, header=header2)
        frames = [(header1, data1), (header2, data2)]
        for i, frame in enumerate(image.frames()):
            header, data = frames[i]
            if i in [0, 1]:
                self.assertIsInstance(frame, fabio.fabioimage.FabioFrame)
                self.assertIs(frame.file_container, image)
                self.assertEqual(frame.header["foo"], header["foo"])
                self.assertEqual(frame.file_index, i)
                self.assertEqual(frame.shape, data.shape)
                self.assertEqual(frame.dtype, data.dtype)
                self.assertTrue(numpy.array_equal(frame.data, data))
            else:
                self.fail()

    def test_tiff_frames(self):
        filename = UtilsTest.getimage("multiframes.tif.bz2")
        filename = filename.replace(".bz2", "")
        image = fabio.open(filename)
        self.assertEqual(image.nframes, 8)
        for i, frame in enumerate(image.frames()):
            if 0 <= i < 8:
                self.assertIsInstance(frame, fabio.fabioimage.FabioFrame)
                self.assertIs(frame.file_container, image)
                self.assertEqual(frame.file_index, i)
                self.assertEqual(frame.data[0, 0], i)
                self.assertEqual(frame.shape, (40, 20))
                self.assertEqual(frame.dtype, numpy.dtype("uint16"))
            else:
                self.fail()


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestFrames))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
