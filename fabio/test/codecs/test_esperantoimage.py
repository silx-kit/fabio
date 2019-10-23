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

"""Test Esperanto images
"""

from __future__ import print_function, with_statement, division, absolute_import

import fabio.esperantoimage
from ..utilstest import UtilsTest

import unittest
import logging

logger = logging.getLogger(__name__)


class TestEsperanto(unittest.TestCase):
    # filename dim1 dim2 min max mean stddev
    TESTIMAGES = [
        ("sucrose_1s__1_1.esperanto.bz2", 2048, 2048, 0, 65535, 8546.6414, 1500.4198)
    ]

    def test_read(self):
        """
        Test the reading of Mar345 images
        """
        for params in self.TESTIMAGES:
            name = params[0]
            logger.debug("Processing: %s" % name)
            dim1, dim2 = params[1:3]
            shape = dim2, dim1
            mini, maxi, mean, stddev = params[3:]
            obj = fabio.esperantoimage.EsperantoImage()
            obj.read(UtilsTest.getimage(name))

            # self.assertAlmostEqual(mini, obj.getmin(), 2, "getmin [%s,%s]" % (mini, obj.getmin()))
            # self.assertAlmostEqual(maxi, obj.getmax(), 2, "getmax [%s,%s]" % (maxi, obj.getmax()))
            # self.assertAlmostEqual(mean, obj.getmean(), 2, "getmean [%s,%s]" % (mean, obj.getmean()))
            # self.assertAlmostEqual(stddev, obj.getstddev(), 2, "getstddev [%s,%s]" % (stddev, obj.getstddev()))

            self.assertEqual(shape, obj.shape, "dim1")

    def test_header(self):
        for params in self.TESTIMAGES:
            name = params[0]
            logger.debug("Processing: %s" % name)
            obj = fabio.esperantoimage.EsperantoImage()
            obj.read(UtilsTest.getimage(name))

            # The key order is not the same depending on Python2 or 3
            expected_keys = set([
                'IMAGE',
                'SPECIAL_CCD_1',
                'SPECIAL_CCD_2',
                'SPECIAL_CCD_3',
                'SPECIAL_CCD_4',
                'SPECIAL_CCD_5',
                'TIME',
                'MONITOR',
                'PIXELSIZE',
                'TIMESTAMP',
                'GRIDPATTERN',
                'STARTANGLESINDEG',
                'ENDANGLESINDEG',
                'GONIOMODEL_1',
                'GONIOMODEL_2',
                'WAVELENGTH',
                'MONOCHROMATOR',
                'ABSTORUN',
                'HISTORY',
                'ESPERANTO_FORMAT'])

            self.assertEqual(set(obj.header.keys()), expected_keys)


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestEsperanto))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
