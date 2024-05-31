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
# THE SOFTWARE.
#

"""
Unit tests for the d*TREK format.
"""

import unittest
import os
import logging
import numpy
import shutil

from ..utilstest import UtilsTest

logger = logging.getLogger(__name__)

import fabio
from fabio.dtrekimage import DtrekImage
from fabio.edfimage import EdfImage
from fabio.utils import testutils

# statistics come from fit2d I think
# filename dim1 dim2 min max mean stddev
TESTIMAGES = [("mb_LP_1_001.img", (3072, 3072), 0.0000, 65535., 120.33, 147.38,
               {"BEAM_CENTER_Y": "157.500000"}),
              ("mb_LP_1_001.img.gz", (3072, 3072), 0.0000, 65535., 120.33, 147.38,
               {"BEAM_CENTER_Y": "157.500000"}),
              ("mb_LP_1_001.img.bz2", (3072, 3072), 0.0000, 65535., 120.33, 147.38,
               {"BEAM_CENTER_Y": "157.500000"}),
              ("HSA_1_5mg_C1_0004.img", (385, 775), -2, 2127, 69.25, 59.52,
               {"WAVELENGTH": "1.0 1.541870"}),
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


class TestDtrekImplementation(testutils.ParametricTestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp_directory = os.path.join(UtilsTest.tempdir, cls.__name__)
        os.makedirs(cls.tmp_directory)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp_directory)

    def setUp(self):
        unittest.TestCase.setUp(self)

    def test_write_and_read_cube(self):
        input_type = numpy.uint16
        data = numpy.arange(5 * 10 * 2).reshape(5, 10, 2)
        data = data.astype(input_type)
        obj = DtrekImage(data=data)
        filename = os.path.join(self.tmp_directory, "cube.img")
        obj.save(filename)
        self.assertEqual(obj.data.dtype.type, input_type)
        obj2 = fabio.open(filename)
        self.assertEqual(obj2.data.dtype.type, input_type)
        self.assertEqual(obj.shape, obj2.shape)
        numpy.testing.assert_array_almost_equal(obj.data, obj2.data)

    def test_write_and_read_empty(self):
        obj = DtrekImage(data=None)
        filename = os.path.join(self.tmp_directory, "cube.img")
        obj.save(filename)
        obj2 = fabio.open(filename)
        self.assertEqual(obj2.data, None)
        self.assertEqual(obj.data, obj2.data)

    def test_write_and_read(self):
        configs = [
            (numpy.uint16, "little_endian", None),
            (numpy.uint16, "big_endian", None),
            (numpy.uint32, "little_endian", None),
            (numpy.int32, "little_endian", None),
            (numpy.float32, "little_endian", None),
            (numpy.float32, "little_endian", None),
            # Data have to be converted before storage
            (numpy.uint64, "little_endian", numpy.uint32),
            (numpy.int64, "little_endian", numpy.int32),
            (numpy.float16, "little_endian", numpy.float32),
        ]
        for config in configs:
            with self.subTest(config=config):
                input_type, byte_order, output_type = config
                if output_type is None:
                    output_type = input_type

                header = {}
                header["BYTE_ORDER"] = byte_order
                data = numpy.arange(5 * 10).reshape(5, 10)
                data = data.astype(input_type)
                obj = DtrekImage(data=data, header=header)
                filename = os.path.join(self.tmp_directory, "saved_%s.img" % hash(config))
                obj.save(filename)
                self.assertEqual(obj.data.dtype.type, input_type)
                obj2 = fabio.open(filename)
                self.assertEqual(obj2.data.dtype.type, output_type)
                self.assertEqual(obj.shape, obj2.shape)
                if input_type == output_type:
                    numpy.testing.assert_array_almost_equal(obj.data, obj2.data)


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
                name, shape, mini, maxi, mean, stddev, keys = datainfo
                obj = DtrekImage()
                obj.read(os.path.join(self.im_dir, name))
                self.assertAlmostEqual(mini, obj.getmin(), 2, "getmin")
                self.assertAlmostEqual(maxi, obj.getmax(), 2, "getmax")
                got_mean = obj.getmean()
                self.assertAlmostEqual(mean, got_mean, 2, "getmean exp %s != got %s" % (mean, got_mean))
                self.assertAlmostEqual(stddev, obj.getstddev(), 2, "getstddev")
                for key, value in keys.items():
                    self.assertIn(key, obj.header)
                    self.assertEqual(value, obj.header[key])
                self.assertEqual(shape, obj.shape)


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestMatch))
    testsuite.addTest(loadTests(TestRealSamples))
    testsuite.addTest(loadTests(TestDtrekImplementation))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
