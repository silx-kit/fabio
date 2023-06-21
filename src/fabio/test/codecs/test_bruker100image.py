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
#bruker100 Unit tests

19/01/2015
"""

import unittest
import os
import logging

logger = logging.getLogger(__name__)

import numpy
from fabio.bruker100image import Bruker100Image, _split_data, _merge_data
from fabio.openimage import openimage
from ..utilstest import UtilsTest

# filename dim1 dim2 min max mean stddev
TESTIMAGES = """NaCl_10_01_0009.sfrm         512 512 -30 5912 34.4626 26.189
                NaCl_10_01_0009.sfrm.gz      512 512 -30 5912 34.4626 26.189
                NaCl_10_01_0009.sfrm.bz2     512 512 -30 5912 34.4626 26.189"""
REFIMAGE = "NaCl_10_01_0009.npy.bz2"


class TestBruker100(unittest.TestCase):
    """ check some read data from bruker version100 detector"""

    def setUp(self):
        """
        download images
        """
        UtilsTest.getimage(REFIMAGE)
        self.im_dir = os.path.dirname(UtilsTest.getimage(TESTIMAGES.split()[0] + ".bz2"))

    def test_read(self):
        """ check we can read bruker100 images"""
        for line in TESTIMAGES.split("\n"):
            vals = line.split()
            name = vals[0]
            dim1, dim2 = [int(x) for x in vals[1:3]]
            shape = dim2, dim1
            mini, maxi, mean, stddev = [float(x) for x in vals[3:]]
            obj = Bruker100Image()
            obj.read(os.path.join(self.im_dir, name))
            self.assertAlmostEqual(mini, obj.getmin(), 2, "getmin")
            self.assertAlmostEqual(maxi, obj.getmax(), 2, "getmax")
            self.assertAlmostEqual(mean, obj.getmean(), 2, "getmean")
            self.assertAlmostEqual(stddev, obj.getstddev(), 2, "getstddev")
            self.assertEqual(shape, obj.shape)

    def test_same(self):
        """ check we can read bruker100 images"""
        ref = openimage(os.path.join(self.im_dir, REFIMAGE))
        for line in TESTIMAGES.split("\n"):
            obt = openimage(os.path.join(self.im_dir, line.split()[0]))
            self.assertTrue(abs(ref.data - obt.data).max() == 0, "data are the same")

    def test_write(self):
        fname = TESTIMAGES.split()[0]
        obt = openimage(os.path.join(self.im_dir, fname))
        name = os.path.basename(fname)

        obj = Bruker100Image(data=obt.data, header=obt.header)
        obj.write(os.path.join(UtilsTest.tempdir, name))
        other = openimage(os.path.join(UtilsTest.tempdir, name))
        self.assertEqual(abs(obt.data - other.data).max(), 0, "data are the same")
        for key in obt.header:
            self.assertTrue(key in other.header, "Key %s is in header" % key)
            self.assertEqual(obt.header[key], other.header[key], "value are the same for key %s" % key)
        os.unlink(os.path.join(UtilsTest.tempdir, name))

    def test_split_merge(self):
        "Pretty challanging random example"
        shape = 256, 256
        outliers = 100
        a = numpy.random.normal(100, 50, size=shape)
        a.ravel()[numpy.random.randint(0, numpy.prod(shape), size=outliers)] = numpy.random.randint(10000, 1000000, size=outliers)
        ref = a.astype("int32")

        for baseline in (None, 0, False):
            split = _split_data(ref, baseline=baseline)
            logger.info("size of underflow: %s overflow1 %s overflow2: %s",
                        split["underflow"].shape, split["overflow1"].shape, split["overflow2"].shape)
            obt = _merge_data(**split)
            self.assertTrue(numpy.allclose(obt, ref), f"data are the same, baseline={baseline}")

    def test_conversion(self):
        fname = UtilsTest.getimage("testcbf.cbf.bz2")[:-4]
        c = openimage(fname)
        assert "Cbf" in c.__class__.__name__, "This is a CbfImage"
        b = c.convert("bruker100")
        fname_out = os.path.join(UtilsTest.tempdir, "testcbf2bruker100.sfrm")
        b.write(fname_out)
        a = openimage(fname_out)
        self.assertTrue(numpy.allclose(a.data, c.data), msg="data are the same")


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestBruker100))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
