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
Test to check TiffIO
"""

import unittest
import os
import logging
import numpy

logger = logging.getLogger(__name__)

from .utilstest import UtilsTest
from ..TiffIO import TiffIO


class TestTiffIO(unittest.TestCase):
    """Test the class format"""

    def write(self, filename):
        tif = TiffIO(filename, mode='wb+')
        dtype = numpy.uint16
        data = numpy.arange(10000).astype(dtype)
        data.shape = 100, 100
        tif.writeImage(data, info={'Title': '1st'})
        tif = None

    def test_write(self):
        filename = "%s.tiff" % self.id()
        filename = os.path.join(UtilsTest.tempdir, filename)
        self.write(filename)

    def test_append(self):
        filename = "%s.tiff" % self.id()
        filename = os.path.join(UtilsTest.tempdir, filename)
        self.write(filename)
        # append
        tif = TiffIO(filename, mode='rb+')
        dtype = numpy.uint16
        data = numpy.arange(100).astype(dtype)
        data.shape = 10, 10
        tif.writeImage((data * 2).astype(dtype), info={'Title': '2nd'})
        self.assertEqual(tif.getNumberOfImages(), 2)
        tif = None

    def test_read(self):
        filename = "%s.tiff" % self.id()
        filename = os.path.join(UtilsTest.tempdir, filename)
        self.write(filename)

        tif = TiffIO(filename)
        self.assertEqual(tif.getNumberOfImages(), 1)
        for i in range(tif.getNumberOfImages()):
            info = tif.getInfo(i)
            for key in info:
                if key not in ["colormap"]:
                    logger.info("%s = %s", key, info[key])
                elif info['colormap'] is not None:
                    logger.info("RED   %s = %s", key, info[key][0:10, 0])
                    logger.info("GREEN %s = %s", key, info[key][0:10, 1])
                    logger.info("BLUE  %s = %s", key, info[key][0:10, 2])
            data = tif.getImage(i)[0, 0:10]
            logger.info("data [0, 0:10] = %s", data)


def suite():
    loader = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loader(TestTiffIO))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
