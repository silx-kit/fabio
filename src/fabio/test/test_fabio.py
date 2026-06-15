# coding: utf-8
#
#    Project: X-ray image reader
#             https://github.com/silx-kit/fabio
#
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
Test the main fabio API.

Basically everything supposed to be provided by `import fabio`
"""

import unittest
import logging
import io
from .utilstest import UtilsTest
import fabio

logger = logging.getLogger(__name__)


class TestFabio(unittest.TestCase):
    def test_open(self):
        filename = UtilsTest.getimage("multiframes.edf.bz2")
        filename = filename.replace(".bz2", "")
        image = fabio.open(filename)
        image.data
        image.close()

    def test_open_bytesio(self):
        filename = UtilsTest.getimage("multiframes.edf.bz2")
        filename = filename.replace(".bz2", "")
        with io.open(filename, "rb") as f:
            data = f.read()
            mem = io.BytesIO(data)
            with fabio.open(mem) as image:
                self.assertIsNotNone(image)
                self.assertEqual(image.nframes, 8)

    def test_open_fabio_bytesio(self):
        filename = UtilsTest.getimage("multiframes.edf.bz2")
        filename = filename.replace(".bz2", "")
        with io.open(filename, "rb") as f:
            data = f.read()
            mem = fabio.fabioutils.BytesIO(data)
            with fabio.open(mem) as image:
                self.assertIsNotNone(image)
                self.assertEqual(image.nframes, 8)

    def test_open_with(self):
        filename = UtilsTest.getimage("multiframes.edf.bz2")
        filename = filename.replace(".bz2", "")
        with fabio.open(filename) as image:
            image.data

    def test_open_series(self):
        filename = UtilsTest.getimage("multiframes.edf.bz2")
        filename = filename.replace(".bz2", "")
        series = fabio.open_series(filenames=[filename])
        for _frame in series.frames():
            pass
        series.close()

    def test_open_series_with(self):
        filename = UtilsTest.getimage("multiframes.edf.bz2")
        filename = filename.replace(".bz2", "")
        with fabio.open_series(filenames=[filename]) as series:
            for _frame in series.frames():
                pass

    def test_open_series_first_filename(self):
        filename = UtilsTest.getimage("multiframes.edf.bz2")
        filename = filename.replace(".bz2", "")
        with fabio.open_series(first_filename=filename) as series:
            for _frame in series.frames():
                pass


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestFabio))
    return testsuite


if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite())
