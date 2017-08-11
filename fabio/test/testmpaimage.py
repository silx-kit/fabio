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
"""Multiwire Unit tests"""
from __future__ import print_function, with_statement, division, absolute_import
import unittest
import sys
import os
from .utilstest import UtilsTest
if __name__ == '__main__':
    import pkgutil
    __path__ = pkgutil.extend_path([os.path.dirname(__file__)], "fabio.test")

logger = UtilsTest.get_logger(__file__)
fabio = sys.modules["fabio"]


class TestMpa(unittest.TestCase):
    """
    Test classe for multiwire (mpa) images
    """
    TESTIMAGES = [
        # filename dim1 dim2 min max mean stddev
        ("mpa_test.mpa", 1024, 1024, 0, 1295, 0.8590, 18.9393),
    ]

    def test_read(self):
        """
        Test the reading of multiwire images
        """
        for imageData in self.TESTIMAGES:
            name, dim1, dim2, mini, maxi, mean, stddev = imageData
            logger.debug("Processing: %s" % name)
            path = UtilsTest.getimage(name + ".bz2")[:-4]

            obj = fabio.mpaimage.MpaImage()
            obj.read(path)

            self.assertAlmostEqual(mini, obj.getmin(), 2, "getmin [%s,%s]" % (mini, obj.getmin()))
            self.assertAlmostEqual(maxi, obj.getmax(), 2, "getmax [%s,%s]" % (maxi, obj.getmax()))
            self.assertAlmostEqual(mean, obj.getmean(), 2, "getmean [%s,%s]" % (mean, obj.getmean()))
            self.assertAlmostEqual(stddev, obj.getstddev(), 2, "getstddev [%s,%s]" % (stddev, obj.getstddev()))
            self.assertEqual(dim1, obj.dim1, "dim1")
            self.assertEqual(dim2, obj.dim2, "dim2")


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestMpa))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
