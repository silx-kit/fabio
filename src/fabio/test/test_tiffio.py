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
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#  .
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#  .
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.
"""
Test to check TiffIO
"""

import unittest
import os
import logging
import numpy
from .utilstest import UtilsTest
from ..TiffIO import TiffIO

logger = logging.getLogger(__name__)


class TestTiffIO(unittest.TestCase):
    """Test the class format"""

    def write(self, filename):
        tif = TiffIO(filename, mode="wb+")
        dtype = numpy.uint16
        data = numpy.arange(10000).astype(dtype)
        data.shape = 100, 100
        tif.writeImage(data, info={"Title": "1st"})
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
        tif = TiffIO(filename, mode="rb+")
        dtype = numpy.uint16
        data = numpy.arange(100).astype(dtype)
        data.shape = 10, 10
        tif.writeImage((data * 2).astype(dtype), info={"Title": "2nd"})
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
                elif info["colormap"] is not None:
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


if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite())
