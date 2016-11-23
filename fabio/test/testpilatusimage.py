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
import sys
import os
if __name__ == '__main__':
    import pkgutil
    __path__ = pkgutil.extend_path([os.path.dirname(__file__)], "fabio.test")
from .utilstest import UtilsTest

logger = UtilsTest.get_logger(__file__)
fabio = sys.modules["fabio"]


class TestPilatus(unittest.TestCase):
    # filename dim1 dim2 min max mean stddev
    TESTIMAGES = """
    lysb_5mg-1.90s_SAXS.bz2 487 619  0 1300 29.4260 17.7367
    lysb_5mg-1.90s_SAXS.gz 487 619  0 1300 29.4260 17.7367 
    lysb_5mg-1.90s_SAXS 487 619  0 1300 29.4260 17.7367
    
    """

    def test_read(self):
        """
        Test the reading of Mar345 images
        """
        for line in self.TESTIMAGES.split('\n'):
            vals = line.strip().split()
            if not vals:
                continue
            name = vals[0]
            logger.debug("Processing: %s" % name)
            dim1, dim2 = [int(x) for x in vals[1:3]]
            mini, maxi, mean, stddev = [float(x) for x in vals[3:]]
            obj = fabio.pilatusimage.PilatusImage()
            obj.read(UtilsTest.getimage(name))

            self.assertAlmostEqual(mini, obj.getmin(), 2, "getmin [%s,%s]" % (mini, obj.getmin()))
            self.assertAlmostEqual(maxi, obj.getmax(), 2, "getmax [%s,%s]" % (maxi, obj.getmax()))
            self.assertAlmostEqual(mean, obj.getmean(), 2, "getmean [%s,%s]" % (mean, obj.getmean()))
            self.assertAlmostEqual(stddev, obj.getstddev(), 2, "getstddev [%s,%s]" % (stddev, obj.getstddev()))
            self.assertEqual(dim1, obj.dim1, "dim1")
            self.assertEqual(dim2, obj.dim2, "dim2")


def suite():
    testsuite = unittest.TestSuite()
    testsuite.addTest(TestPilatus("test_read"))
    return testsuite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
