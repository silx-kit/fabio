#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Project: Fable Input Output
#             https://github.com/silx-kit/fabio
#
#    Copyright (C) European Synchrotron Radiation Facility, Grenoble, France
#
#    Principal author:       Jérôme Kieffer (Jerome.Kieffer@ESRF.eu)
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

"""Test Eiger images
"""

import unittest
import os
import logging

logger = logging.getLogger(__name__)

from fabio.openimage import openimage
from fabio.limaimage import LimaImage, h5py
from ..utilstest import UtilsTest
from ..test_frames import _CommonTestFrames


def make_hdf5(name, shape=(50, 99, 101)):
    if h5py is None:
        raise unittest.SkipTest("h5py is not available")

    with h5py.File(name, mode="w") as h:
        h.attrs["creator"] = "LIMA"
        h.attrs["default"] = "/entry"
        e = h.require_group("/entry/measurement")        
        if len(shape) == 2:
            e.require_dataset("data", shape, compression="gzip", compression_opts=9, dtype="uint16")
        elif len(shape) == 3:
            e.require_dataset("data", shape, chunks=(1,) + shape[1:], compression="gzip", compression_opts=9, dtype="uint16")


class TestLima(_CommonTestFrames):
    """basic test"""

    @classmethod
    def setUpClass(cls):
        cls.fn3 = os.path.join(UtilsTest.tempdir, "lima3d.h5")
        print(cls.fn3 )
        make_hdf5(cls.fn3, (17, 99, 101))
        super(TestLima, cls).setUpClass()

    @classmethod
    def getMeta(cls):
        filename = cls.fn3

        class Meta(object):
            pass

        meta = Meta()
        meta.image = None
        meta.filename = filename
        meta.nframes = 17
        return meta

    @classmethod
    def tearDownClass(cls):
        super(TestLima, cls).tearDownClass()
        if os.path.exists(cls.fn3):
            os.unlink(cls.fn3)

    def test_read(self):
        """test_read check we can read images from Lima"""
        e = LimaImage()
        e.read(self.fn3)
        self.assertEqual(e.shape, (99, 101))
        self.assertEqual(e.nframes, 17, "nframe: got %s!=17" % e.nframes)
        self.assertEqual(e.bpp, 2, "bpp OK")

    def test_open(self):
        """test_open check we can read images from Lima"""
        e = openimage(self.fn3)
        self.assertEqual(e.shape, (99, 101))
        self.assertEqual(e.nframes, 17, "nframe: got %s!=17" % e.nframes)
        self.assertEqual(e.bpp, 2, "bpp OK")

def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestLima))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
