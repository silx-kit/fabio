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
Deep test to check IOError exceptions
"""

from __future__ import print_function, with_statement, division, absolute_import

import unittest
import os
import logging

logger = logging.getLogger(__name__)

import fabio
from ..utilstest import UtilsTest
from ..test_frames import _CommonTestFrames


class TestPixiImage(_CommonTestFrames):
    """Test the class format"""

    @classmethod
    def setUpClass(cls):
        cls.create_fake_images()
        super(TestPixiImage, cls).setUpClass()

    @classmethod
    def getMeta(cls):
        class Meta(object):
            pass
        meta = Meta()
        meta.image = None
        meta.filename = cls.multi_frame
        meta.nframes = 3
        return meta

    @classmethod
    def create_fake_images(cls):
        """Create PiXi image.

        This images was generated using our Python code as specification.
        Then it's not a very good way to test our code.
        """
        frame1 = b"\x01\x00" * 476 + b"\x00\x00" * 476 * 511
        frame2 = b"\x02\x00" * 476 + b"\x00\x00" * 476 * 511
        frame3 = b"\x03\x00" * 476 + b"\x00\x00" * 476 * 511
        header = b"\n\xb8\x03\x00" + b"\x00" * 20

        cls.single_frame = os.path.join(UtilsTest.tempdir, "pixi_1frame.dat")
        with open(cls.single_frame, 'wb') as f:
            f.write(header)
            f.write(frame1)

        cls.multi_frame = os.path.join(UtilsTest.tempdir, "pixi_3frame.dat")
        with open(cls.multi_frame, 'wb') as f:
            f.write(header)
            f.write(frame1)
            f.write(header)
            f.write(frame2)
            f.write(header)
            f.write(frame3)

        template = os.path.join(UtilsTest.tempdir, "pixi_series.dat") + "$%04d"
        cls.file_series = template % 0
        frames = [frame1, frame2, frame3]
        for num, frame in enumerate(frames):
            filename = template % num
            with open(filename, 'wb') as f:
                f.write(header)
                f.write(frame)

    def test_single_frame(self):
        image = fabio.open(self.single_frame)
        self.assertEqual(image.nframes, 1)
        self.assertEqual(image.data.shape, (512, 476))
        self.assertEqual(image.data[0, 0], 1)
        self.assertEqual(image.data[1, 1], 0)

    def test_multi_frame(self):
        image = fabio.open(self.multi_frame)
        self.assertEqual(image.nframes, 3)
        self.assertEqual(image.data.shape, (512, 476))
        self.assertEqual(image.data[0, 0], 1)
        self.assertEqual(image.data[1, 1], 0)
        frame = image.getframe(0)
        self.assertEqual(frame.data[0, 0], 1)
        self.assertEqual(frame.data[1, 1], 0)
        frame = image.getframe(1)
        self.assertEqual(frame.data[0, 0], 2)
        self.assertEqual(frame.data[1, 1], 0)
        frame = image.getframe(2)
        self.assertEqual(frame.data[0, 0], 3)
        self.assertEqual(frame.data[1, 1], 0)

    def test_file_series(self):
        image = fabio.open(self.file_series)
        # self.assertEqual(image.nframes, 3)
        self.assertEqual(image.data.shape, (512, 476))
        self.assertEqual(image.data[0, 0], 1)
        self.assertEqual(image.data[1, 1], 0)
        frame = image.getframe(0)
        self.assertEqual(frame.data[0, 0], 1)
        self.assertEqual(frame.data[1, 1], 0)
        frame = image.getframe(1)
        self.assertEqual(frame.data[0, 0], 2)
        self.assertEqual(frame.data[1, 1], 0)
        frame = image.getframe(2)
        self.assertEqual(frame.data[0, 0], 3)
        self.assertEqual(frame.data[1, 1], 0)
        # use the frame to move to another frame
        frame = frame.getframe(0)
        self.assertEqual(frame.data[0, 0], 1)
        self.assertEqual(frame.data[1, 1], 0)


def suite():
    loader = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loader(TestPixiImage))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
