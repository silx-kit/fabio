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
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#  .
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#  .
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.

"""Test failing files"""

import unittest
import os
import io
import fabio
import shutil
from .utilstest import UtilsTest


class TestFailingFiles(unittest.TestCase):
    """Test failing files"""

    @classmethod
    def setUpClass(cls):
        cls.tmp_directory = os.path.join(UtilsTest.tempdir, cls.__name__)
        os.makedirs(cls.tmp_directory)
        cls.createResources(cls.tmp_directory)

    @classmethod
    def createResources(cls, directory):
        cls.txt_filename = os.path.join(directory, "test.txt")
        with io.open(cls.txt_filename, "w+t") as f:
            f.write("Kikoo")

        cls.bad_edf_filename = os.path.join(directory, "bad_edf.edf")
        with io.open(cls.bad_edf_filename, "w+b") as f:
            f.write(b"\r{")
            f.write(b"\x00\xff\x99" * 10)

        cls.bad_edf2_filename = os.path.join(directory, "bad_edf2.edf")
        with io.open(cls.bad_edf2_filename, "w+b") as f:
            f.write(b"\n{\n\n}\n")
            f.write(b"\xff\x00\x99" * 10)

        cls.bad_msk_filename = os.path.join(directory, "bad_msk.msk")
        with io.open(cls.bad_msk_filename, "w+b") as f:
            f.write(b"M\x00\x00\x00A\x00\x00\x00S\x00\x00\x00K\x00\x00\x00")
            f.write(b"\x00\xff\x99" * 10)

        cls.bad_dm3_filename = os.path.join(directory, "bad_dm3.dm3")
        with io.open(cls.bad_dm3_filename, "w+b") as f:
            f.write(b"\x00\x00\x00\x03")
            f.write(b"\x00\xff\x99" * 10)

        cls.bad_npy_filename = os.path.join(directory, "bad_numpy.npy")
        with io.open(cls.bad_npy_filename, "w+b") as f:
            f.write(b"\x93NUMPY")
            f.write(b"\x00\xff\x99" * 10)

        cls.missing_filename = os.path.join(directory, "test.missing")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp_directory)

    def test_missing_file(self):
        self.assertRaises(IOError, fabio.open, self.missing_filename)

    def test_wrong_format(self):
        self.assertRaises(IOError, fabio.open, self.txt_filename)

    def test_wrong_edf(self):
        self.assertRaises(IOError, fabio.open, self.bad_edf_filename)

    def test_wrong_edf2(self):
        self.assertRaises(IOError, fabio.open, self.bad_edf_filename)

    def test_wrong_msk(self):
        self.assertRaises(ValueError, fabio.open, self.bad_msk_filename)

    def test_wrong_dm3(self):
        self.assertRaises(ValueError, fabio.open, self.bad_dm3_filename)

    def test_wrong_numpy(self):
        self.assertRaises(ValueError, fabio.open, self.bad_npy_filename)


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestFailingFiles))
    return testsuite


if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite())
