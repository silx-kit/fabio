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
Unit tests for the Fit2D spread sheet image format.
"""
from __future__ import print_function, with_statement, division, absolute_import

import unittest
import os
import logging

from ..utilstest import UtilsTest

logger = logging.getLogger(__name__)

from fabio.fit2dspreadsheetimage import Fit2dSpreadsheetImage
from fabio.utils import testutils


# statistics come from fit2d I think
# filename dim1 dim2 min max mean stddev
TESTIMAGES = [("example.spr", (512, 512), 86.0, 61204.0, 511.63, 667.148),
              ("example.spr.gz", (512, 512), 86.0, 61204.0, 511.63, 667.148),
              ("example.spr.bz2", (512, 512), 86.0, 61204.0, 511.63, 667.148),
              ]


class TestRealSamples(testutils.ParametricTestCase):
    """
    Test real samples stored in our archive.
    """

    @classmethod
    def setUpClass(cls):
        """Prefetch images"""
        download = []
        for datainfo in TESTIMAGES:
            name = datainfo[0]
            if name.endswith(".bz2"):
                download.append(name)
            elif name.endswith(".gz"):
                download.append(name[:-3] + ".bz2")
            else:
                download.append(name + ".bz2")
        download = list(set(download))
        for name in download:
            os.path.dirname(UtilsTest.getimage(name))
        cls.im_dir = UtilsTest.resources.data_home

    def test_read(self):
        """ check we can read flat ADSC images"""
        for datainfo in TESTIMAGES:
            with self.subTest(datainfo=datainfo):
                name, shape, mini, maxi, mean, stddev = datainfo
                obj = Fit2dSpreadsheetImage()
                obj.read(os.path.join(self.im_dir, name))
                self.assertAlmostEqual(mini, obj.getmin(), 2, "getmin")
                self.assertAlmostEqual(maxi, obj.getmax(), 2, "getmax")
                got_mean = obj.getmean()
                self.assertAlmostEqual(mean, got_mean, 2, "getmean")
                self.assertAlmostEqual(stddev, obj.getstddev(), 2, "getstddev")
                self.assertEqual(shape, obj.shape)


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestRealSamples))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
