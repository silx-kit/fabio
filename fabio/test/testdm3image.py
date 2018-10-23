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
# Unit tests

# builds on stuff from ImageD11.test.testpeaksearch

Updated by Jerome Kieffer (jerome.kieffer@esrf.eu), 2011

"""


from __future__ import print_function, with_statement, division, absolute_import

__date__ = "22/10/2018"
__author__ = "jerome Kieffer"


import unittest
import os
import logging

logger = logging.getLogger(__name__)

import fabio
from fabio.dm3image import Dm3Image
from .utilstest import UtilsTest

# statistics come from fit2d I think
# filename dim1 dim2 min max mean stddev
TESTIMAGES = """ref_d20x_310mm.dm3     2048 2048 -31842.354 23461.672 569.38782 1348.4183
                ref_d20x_310mm.dm3.gz  2048 2048 -31842.354 23461.672 569.38782 1348.4183
                ref_d20x_310mm.dm3.bz2 2048 2048 -31842.354 23461.672 569.38782 1348.4183"""


class TestDm3Image(unittest.TestCase):
    """
    """
    def setUp(self):
        """ Download images """
        self.im_dir = os.path.dirname(UtilsTest.getimage("ref_d20x_310mm.dm3.bz2"))

    def test_read(self):
        """ check we can read dm3 images"""
        for line in TESTIMAGES.split("\n"):
            vals = line.split()
            name = vals[0]
            dim1, dim2 = [int(x) for x in vals[1:3]]
            mini, maxi, mean, stddev = [float(x) for x in vals[3:]]
            fname = os.path.join(self.im_dir, name)
            obj1 = Dm3Image()
            obj1.read(fname)
            obj2 = fabio.open(fname)
            for obj in (obj1, obj2):
                self.assertAlmostEqual(mini, obj.getmin(), 2, "getmin")
                self.assertAlmostEqual(maxi, obj.getmax(), 2, "getmax")
                got_mean = obj.getmean()
                self.assertAlmostEqual(mean, got_mean, 2, "getmean exp %s != got %s" % (mean, got_mean))
                self.assertAlmostEqual(stddev, obj.getstddev(), 2, "getstddev")
                self.assertEqual(dim1, obj.dim1, "dim1")
                self.assertEqual(dim2, obj.dim2, "dim2")


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestDm3Image))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
