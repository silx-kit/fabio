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
import numpy
from fabio.openimage import openimage
from fabio.eigerimage import EigerImage, h5py
from ..utilstest import UtilsTest
from ..test_frames import _CommonTestFrames


def make_hdf5(name, shape=(50, 99, 101)):
    if h5py is None:
        raise unittest.SkipTest("h5py is not available")

    with h5py.File(name, mode="w") as h:
        e = h.require_group("entry/data")
        if len(shape) == 2:
            e.require_dataset("data", shape, compression="gzip", compression_opts=9, dtype="float32")
        elif len(shape) == 3:
            e.require_dataset("data", shape, chunks=(1,) + shape[1:], compression="gzip", compression_opts=9, dtype="float32")


class TestEiger(_CommonTestFrames):
    """basic test"""

    @classmethod
    def setUpClass(cls):
        cls.fn3 = os.path.join(UtilsTest.tempdir, "eiger3d.h5")
        make_hdf5(cls.fn3, (50, 99, 101))
        super(TestEiger, cls).setUpClass()

    @classmethod
    def getMeta(cls):
        filename = cls.fn3

        class Meta(object):
            pass

        meta = Meta()
        meta.image = None
        meta.filename = filename
        meta.nframes = 50
        return meta

    @classmethod
    def tearDownClass(cls):
        super(TestEiger, cls).tearDownClass()
        if os.path.exists(cls.fn3):
            os.unlink(cls.fn3)

    def test_read(self):
        """ check we can read images from Eiger"""
        e = EigerImage()
        e.read(self.fn3)
        self.assertEqual(e.shape, (99, 101))
        self.assertEqual(e.nframes, 50, "nframe: got %s!=50" % e.nframes)
        self.assertEqual(e.bpp, 4, "bpp OK")

    def test_open(self):
        """ check we can read images from Eiger"""
        e = openimage(self.fn3)
        self.assertEqual(e.shape, (99, 101))
        self.assertEqual(e.nframes, 50, "nframe: got %s!=50" % e.nframes)
        self.assertEqual(e.bpp, 4, "bpp OK")

    def test_write(self):
        fn = os.path.join(UtilsTest.tempdir, "eiger_write.h5")
        shape = (10, 11, 13)
        ary = numpy.random.randint(0, 100, size=shape)
        e = EigerImage()
        for i, d in enumerate(ary):
            e.set_data(d, i)
        self.assertEqual(shape[0], e.nframes, "shape matches")
        self.assertEqual(shape[1:], e.shape, "shape matches")
        e.save(fn)
        self.assertTrue(os.path.exists(fn), "file exists")
        f = openimage(fn)
        self.assertEqual(str(f.__class__.__name__), "EigerImage", "Used the write reader")
        self.assertEqual(shape[0], f.nframes, "shape matches")
        self.assertEqual(shape[1:], f.shape, "shape matches")
        self.assertEqual(abs(f.data - ary[0]).max(), 0, "first frame matches")
        for i, g in enumerate(f):
            self.assertEqual(abs(g.data - ary[i]).max(), 0, f"frame {i} matches")

    def test_bug_479(self):
        fn = os.path.join(UtilsTest.tempdir, "eiger_479.h5")
        r = numpy.random.randint(0, 100, size=(100, 101))
        e = EigerImage(data=r)
        e.write(fn)
        f = openimage(fn)
        self.assertEqual(f.data.shape, r.shape, "shape match")
        self.assertEqual(f.nframes, e.nframes, "nframes match")
        self.assertTrue(numpy.all(f.data == e.data), "data match")


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestEiger))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
