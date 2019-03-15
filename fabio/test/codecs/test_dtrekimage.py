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
28/11/2014
"""
from __future__ import print_function, with_statement, division, absolute_import

import unittest
import os
import logging

from ..utilstest import UtilsTest

logger = logging.getLogger(__name__)

from fabio.dtrekimage import DtrekImage
from fabio.edfimage import EdfImage
from fabio.utils import testutils


# statistics come from fit2d I think
# filename dim1 dim2 min max mean stddev
TESTIMAGES = [("mb_LP_1_001.img", (3072, 3072), 0.0000, 65535., 120.33, 147.38),
              ("mb_LP_1_001.img.gz", (3072, 3072), 0.0000, 65535., 120.33, 147.38),
              ("mb_LP_1_001.img.bz2", (3072, 3072), 0.0000, 65535., 120.33, 147.38),
              ("HSA_1_5mg_C1_0004.img", (385, 775), -2, 2127, 69.25, 59.52),
              ]


class TestMatch(unittest.TestCase):
    """
    check the ??fit2d?? conversion to edf gives same numbers
    """
    def setUp(self):
        """ Download images """
        self.fn_adsc = UtilsTest.getimage("mb_LP_1_001.img.bz2")[:-4]
        self.fn_edf = UtilsTest.getimage("mb_LP_1_001.edf.bz2")[:-4]

    def testsame(self):
        """test ADSC image match to EDF"""
        im1 = EdfImage()
        im1.read(self.fn_edf)
        im2 = DtrekImage()
        im2.read(self.fn_adsc)
        diff = (im1.data.astype("float32") - im2.data.astype("float32"))
        logger.debug("type: %s %s shape %s %s " % (im1.data.dtype, im2.data.dtype, im1.data.shape, im2.data.shape))
        logger.debug("im1 min %s %s max %s %s " % (im1.data.min(), im2.data.min(), im1.data.max(), im2.data.max()))
        logger.debug("delta min %s max %s mean %s" % (diff.min(), diff.max(), diff.mean()))
        self.assertEqual(abs(diff).max(), 0.0, "asdc data == edf data")


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
                obj = DtrekImage()
                obj.read(os.path.join(self.im_dir, name))
                self.assertAlmostEqual(mini, obj.getmin(), 2, "getmin")
                self.assertAlmostEqual(maxi, obj.getmax(), 2, "getmax")
                got_mean = obj.getmean()
                self.assertAlmostEqual(mean, got_mean, 2, "getmean exp %s != got %s" % (mean, got_mean))
                self.assertAlmostEqual(stddev, obj.getstddev(), 2, "getstddev")
                self.assertEqual(shape, obj.shape)


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestMatch))
    testsuite.addTest(loadTests(TestRealSamples))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
