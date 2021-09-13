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
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.#

"""Test Esperanto images
"""

import os
import fabio.esperantoimage
from ..utilstest import UtilsTest

import unittest
import logging
import numpy
logger = logging.getLogger(__name__)


class TestEsperanto(unittest.TestCase):
    # filename dim1 dim2 min max mean stddev
    TESTIMAGES = [
        ("sucrose_1s__1_1.esperanto.bz2", 2048, 2048, -173, 66043, 16.31592893600464, 266.4471326013064),  # To validate
        ("reference.esperanto.bz2", 256, 256, -1, 10963, 1.767120361328125, 50.87154169213312)
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

            self.assertAlmostEqual(mini, obj.getmin(), 2, "getmin [%s,%s]" % (mini, obj.getmin()))
            self.assertAlmostEqual(maxi, obj.getmax(), 2, "getmax [%s,%s]" % (maxi, obj.getmax()))
            self.assertAlmostEqual(mean, obj.getmean(), 2, "getmean [%s,%s]" % (mean, obj.getmean()))
            self.assertAlmostEqual(stddev, obj.getstddev(), 2, "getstddev [%s,%s]" % (stddev, obj.getstddev()))

            self.assertEqual(shape, obj.shape, "dim1")

    def test_header(self):
        for params in self.TESTIMAGES:
            name = params[0]
            logger.debug("Processing: %s" % name)
            obj = fabio.esperantoimage.EsperantoImage()
            obj.read(UtilsTest.getimage(name))

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
                'ESPERANTO FORMAT'])

            upper_keys = set(i for i in obj.header.keys() if i.isupper())
            self.assertEqual(upper_keys, expected_keys)

            # Test write uncompressed:
            obj.format = "4BYTE_LONG"
            dst = os.path.join(UtilsTest.tempdir, "4bytes_long.esperanto")
            logger.info("Saving tmp file to %s", dst)
            obj.write(dst)

            new = fabio.open(dst)
            self.assertTrue(numpy.allclose(obj.data, new.data), msg="data are the same")
            for k, v in obj.header.items():
                if k not in ("ESPERANTO FORMAT",
                             ):
                    self.assertEqual(v, new.header.get(k), "header differ on %s: %s vs %s" % (k, v, new.header.get(k)))

            # Test write compressed:
            obj.format = "AGI_BITFIELD"
            dst = os.path.join(UtilsTest.tempdir, "agi_bitfield.esperanto")
            logger.info("Saving tmp file to %s", dst)
            obj.write(dst)

            new = fabio.open(dst)
            self.assertTrue(numpy.allclose(obj.data, new.data), msg="data are the same")
            for k, v in obj.header.items():
                if k not in ("ESPERANTO FORMAT",
                             ):
                    self.assertEqual(v, new.header.get(k), "header differ on %s: %s vs %s" % (k, v, new.header.get(k)))

    def test_data(self):
        a = (numpy.random.random((257, 421)) * 100).round()
        e = fabio.esperantoimage.EsperantoImage(data=a)
        self.assertEqual(e.data.dtype, numpy.int32, "dtype has been changed")
        self.assertEqual(e.data.shape, (424, 424), "data has been resized")
        self.assertAlmostEqual(a.sum(), e.data.sum(), 2, "conent is almost the same")

    def test_values(self):
        esp = fabio.open(UtilsTest.getimage("reference.esperanto.bz2")[:-4])
        npy = fabio.open(UtilsTest.getimage("reference.npy.bz2")[:-4])
        self.assertEqual(numpy.alltrue(esp.data == npy.data), True, "Images are the same")


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestEsperanto))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
