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
Test the main fabio API.

Basically everything supposed to be provided by `import fabio`
"""

import unittest
import logging
import io

logger = logging.getLogger(__name__)

from .utilstest import UtilsTest
import fabio


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


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
