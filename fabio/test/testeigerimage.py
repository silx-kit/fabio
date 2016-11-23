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

"""Test Eiger images
"""

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

from fabio.openimage import openimage
from fabio.eigerimage import EigerImage, h5py


def make_hdf5(name, shape=(50, 99, 101)):
    with h5py.File(name) as h:
        e = h.require_group("entry/data")
        if len(shape) == 2:
            e.require_dataset("data", shape, compression="gzip", compression_opts=9, dtype="float32")
        elif len(shape) == 3:
            e.require_dataset("data", shape, chunks=(1,) + shape[1:], compression="gzip", compression_opts=9, dtype="float32")


class TestEiger(unittest.TestCase):
    """basic test"""

    @classmethod
    def setUpClass(cls):
        super(TestEiger, cls).setUpClass()
        cls.fn3 = os.path.join(UtilsTest.tempdir, "eiger3d.h5")
        make_hdf5(cls.fn3, (50, 99, 101))

    @classmethod
    def tearDownClass(cls):
        super(TestEiger, cls).tearDownClass()
        if os.path.exists(cls.fn3):
            os.unlink(cls.fn3)

    def test_read(self):
        """ check we can read images from Eiger"""
        e = EigerImage()
        e.read(self.fn3)
        self.assertEqual(e.dim1, 101, "dim1 OK")
        self.assertEqual(e.dim2, 99, "dim2 OK")
        self.assertEqual(e.nframes, 50, "nframe: got %s!=50" % e.nframes)
        self.assertEqual(e.bpp, 4, "bpp OK")

    def test_open(self):
        """ check we can read images from Eiger"""
        e = openimage(self.fn3)
        self.assertEqual(e.dim1, 101, "dim1 OK")
        self.assertEqual(e.dim2, 99, "dim2 OK")
        self.assertEqual(e.nframes, 50, "nframe: got %s!=50" % e.nframes)
        self.assertEqual(e.bpp, 4, "bpp OK")


def suite():
    testsuite = unittest.TestSuite()
    if h5py is not None:
        testsuite.addTest(TestEiger("test_read"))
        testsuite.addTest(TestEiger("test_open"))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
