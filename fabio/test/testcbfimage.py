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
2011: Jerome Kieffer for ESRF.

Unit tests for CBF images based on references images taken from:
http://pilatus.web.psi.ch/DATA/DATASETS/insulin_0.2/

19/01/2015
"""
from __future__ import print_function, with_statement, division, absolute_import
import unittest
import sys
import os
import numpy
import gzip
import bz2
import time

if __name__ == '__main__':
    import pkgutil
    __path__ = pkgutil.extend_path([os.path.dirname(__file__)], "fabio.test")
from .utilstest import UtilsTest

logger = UtilsTest.get_logger(__file__)
fabio = sys.modules["fabio"]
from fabio.cbfimage import cbfimage
from fabio.compression import decByteOffset_numpy, decByteOffset_cython
from fabio.third_party.six import PY3
if PY3:
    from fabio.fabioutils import unicode


class TestCbfReader(unittest.TestCase):
    """ test cbf image reader """

    def __init__(self, methodName):
        "Constructor of the class"
        unittest.TestCase.__init__(self, methodName)
        self.edf_filename = os.path.join(UtilsTest.image_home, "run2_1_00148.edf")
        self.cbf_filename = os.path.join(UtilsTest.image_home, "run2_1_00148.cbf")

    def setUp(self):
        """Download images"""

        UtilsTest.getimage(os.path.basename(self.edf_filename + ".bz2"))
        UtilsTest.getimage(os.path.basename(self.cbf_filename + ".bz2"))

    def test_read(self):
        """ check whole reader"""
        times = []
        times.append(time.time())
        cbf = fabio.open(self.cbf_filename)
        times.append(time.time())
        edf = fabio.open(self.edf_filename)
        times.append(time.time())

        self.assertAlmostEqual(0, abs(cbf.data - edf.data).max())
        logger.info("Reading CBF took %.3fs whereas the same EDF took %.3fs" % (times[1] - times[0], times[2] - times[1]))

    def test_write(self):
        "Rest writing with self consistency at the fabio level"
        name = os.path.basename(self.cbf_filename)
        obj = cbfimage()
        obj.read(self.cbf_filename)
        obj.write(os.path.join(UtilsTest.tempdir, name))
        other = cbfimage()
        other.read(os.path.join(UtilsTest.tempdir, name))
        self.assertEqual(abs(obj.data - other.data).max(), 0, "data are the same")
        for key in obj.header:
            if key in["filename", "X-Binary-Size-Padding"]:
                continue
            self.assertTrue(key in other.header, "Key %s is in header" % key)
            self.assertEqual(obj.header[key], other.header[key], "value are the same for key %s" % key)
        os.unlink(os.path.join(UtilsTest.tempdir, name))

    def test_byte_offset(self):
        """ check byte offset algorithm"""
        cbf = fabio.open(self.cbf_filename)
        starter = b"\x0c\x1a\x04\xd5"
        cbs = cbf.cbs
        startPos = cbs.find(starter) + 4
        data = cbs[startPos: startPos + int(cbf.header["X-Binary-Size"])]
        startTime = time.time()
        numpyRes = decByteOffset_numpy(data, size=cbf.dim1 * cbf.dim2)
        tNumpy = time.time() - startTime
        logger.info("Timing for Numpy method : %.3fs" % tNumpy)

        startTime = time.time()
        cythonRes = decByteOffset_cython(stream=data, size=cbf.dim1 * cbf.dim2)
        tCython = time.time() - startTime
        delta = abs(numpyRes - cythonRes).max()
        self.assertAlmostEqual(0, delta)
        logger.info("Timing for Cython method : %.3fs, max delta= %s" % (tCython, delta))

    def test_consitency_manual(self):
        """
        Test if an image can be read and saved and the results are "similar"
        """
        name = os.path.basename(self.cbf_filename)
        obj = fabio.open(self.cbf_filename)
        new = fabio.cbfimage.cbfimage(data=obj.data, header=obj.header)
        new.write(os.path.join(UtilsTest.tempdir, name))
        other = fabio.open(os.path.join(UtilsTest.tempdir, name))
        self.assertEqual(abs(obj.data - other.data).max(), 0, "data are the same")
        for key in obj.header:
            if key in["filename", "X-Binary-Size-Padding"]:
                continue
            self.assertTrue(key in other.header, "Key %s is in header" % key)
            self.assertEqual(obj.header[key], other.header[key], "value are the same for key %s [%s|%s]" % (key, obj.header[key], other.header[key]))

    def test_consitency_convert(self):
        """
        Test if an image can be read and saved and the results are "similar"
        """
        name = os.path.basename(self.cbf_filename)
        obj = fabio.open(self.cbf_filename)
        new = obj.convert("cbf")
        new.write(os.path.join(UtilsTest.tempdir, name))
        other = fabio.open(os.path.join(UtilsTest.tempdir, name))
        self.assertEqual(abs(obj.data - other.data).max(), 0, "data are the same")
        for key in obj.header:
            if key in["filename", "X-Binary-Size-Padding"]:
                continue
            self.assertTrue(key in other.header, "Key %s is in header" % key)
            self.assertEqual(obj.header[key], other.header[key], "value are the same for key %s [%s|%s]" % (key, obj.header[key], other.header[key]))

    def test_unicode(self):
        """
        Test if an image can be read and saved to an unicode named
        """
        name = unicode(os.path.basename(self.cbf_filename))
        obj = fabio.open(self.cbf_filename)
        obj.write(os.path.join(UtilsTest.tempdir, name))
        other = fabio.open(os.path.join(UtilsTest.tempdir, name))
        self.assertEqual(abs(obj.data - other.data).max(), 0, "data are the same")
        for key in obj.header:
            if key in["filename", "X-Binary-Size-Padding"]:
                continue
            self.assertTrue(key in other.header, "Key %s is in header" % key)
            self.assertEqual(obj.header[key], other.header[key], "value are the same for key %s [%s|%s]" % (key, obj.header[key], other.header[key]))


def suite():
    testsuite = unittest.TestSuite()
    testsuite.addTest(TestCbfReader("test_read"))
    testsuite.addTest(TestCbfReader("test_write"))
    testsuite.addTest(TestCbfReader("test_byte_offset"))
    testsuite.addTest(TestCbfReader("test_consitency_manual"))
    testsuite.addTest(TestCbfReader("test_consitency_convert"))
    testsuite.addTest(TestCbfReader("test_unicode"))

    return testsuite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())

