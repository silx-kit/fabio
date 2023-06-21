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

import unittest
import os
import logging

logger = logging.getLogger(__name__)

from .utilstest import UtilsTest
import fabio


class TestImageConvert(unittest.TestCase):
    """Test image convertions"""

    def test_edf_to_tiff(self):
        tmpdir = os.path.join(UtilsTest.tempdir, self.id())
        os.mkdir(tmpdir)

        filename = UtilsTest.getimage("face.edf")
        output_filename = os.path.join(tmpdir, "face.tif")

        image = fabio.open(filename)
        image2 = image.convert("tiff")
        image2.save(output_filename)
        self.assertEqual(image.shape, image2.shape)
        image3 = fabio.open(output_filename)
        self.assertEqual(image.shape, image3.shape)


def suite():
    loader = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loader(TestImageConvert))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
