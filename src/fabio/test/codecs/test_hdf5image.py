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

"""Test Eiger images
"""

import unittest
import os
import logging

logger = logging.getLogger(__name__)

from fabio.fabioutils import exists
from fabio.openimage import openimage
from fabio.hdf5image import Hdf5Image, h5py
from ..utilstest import UtilsTest


def make_hdf5(name, shape=(50, 99, 101)):
    if h5py is None:
        raise unittest.SkipTest("h5py is not available")

    with h5py.File(name, mode="w") as h:
        e = h.require_group("entry")
        if len(shape) == 2:
            e.require_dataset("data", shape, compression="gzip", compression_opts=9, dtype="float32")
        elif len(shape) == 3:
            e.require_dataset("data", shape, chunks=(1,) + shape[1:], compression="gzip", compression_opts=9, dtype="float32")
    return name + "::entry/data"


class TestHdf5(unittest.TestCase):
    """basic test"""

    @classmethod
    def setUpClass(cls):
        super(TestHdf5, cls).setUpClass()
        cls.fn2 = os.path.join(UtilsTest.tempdir, "eiger2d.h5")
        cls.fn2 = make_hdf5(cls.fn2, (99, 101))
        cls.fn3 = os.path.join(UtilsTest.tempdir, "eiger3d.h5")
        cls.fn3 = make_hdf5(cls.fn3, (50, 99, 101))

    @classmethod
    def tearDownClass(cls):
        super(TestHdf5, cls).tearDownClass()
        if exists(cls.fn3):
            os.unlink(cls.fn3.split("::")[0])
        if exists(cls.fn2):
            os.unlink(cls.fn2.split("::")[0])

    def test_read(self):
        """ check we can read images from Eiger"""
        e = Hdf5Image()
        e.read(self.fn2)
        self.assertEqual(e.shape, (99, 101))
        self.assertEqual(e.nframes, 1, "nframes OK")
        self.assertEqual(e.bpp, 4, "nframes OK")

        e = Hdf5Image()
        e.read(self.fn3)
        self.assertEqual(e.shape, (99, 101))
        self.assertEqual(e.nframes, 50, "nframes OK")
        self.assertEqual(e.bpp, 4, "nframes OK")

    def test_open(self):
        """ check we can read images from Eiger"""
        e = openimage(self.fn2)
        self.assertEqual(e.shape, (99, 101))
        self.assertEqual(e.nframes, 1, "nframes OK")
        self.assertEqual(e.bpp, 4, "nframes OK")

        e = openimage(self.fn3)
        self.assertEqual(e.shape, (99, 101))
        self.assertEqual(e.nframes, 50, "nframes OK")
        self.assertEqual(e.bpp, 4, "nframes OK")

    def test_next_frames(self):
        """ check the legacy next API"""
        h5 = openimage(self.fn3)
        frame_nb = 1
        frame_id = 0
        frame = h5
        while True:
            try:
                frame = frame.next()
                frame_id = frame.file_index
                frame_nb += 1
            except IndexError:
                break
        self.assertEqual(frame_nb, 50)
        self.assertEqual(frame_id, 49)

    def test_iterate(self):
        for i, f in enumerate(openimage(self.fn3)):
            print(i, f)
        self.assertEqual(i, 49, "Last frame is #49")


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestHdf5))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
