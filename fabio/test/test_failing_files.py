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

"""Test failing files
"""

from __future__ import print_function, with_statement, division, absolute_import

import unittest
import os
import io
import fabio
import tempfile
import shutil
import sys


class TestFailingFiles(unittest.TestCase):
    """Test failing files"""

    @classmethod
    def setUpClass(cls):
        cls.tmp_directory = tempfile.mkdtemp()
        cls.createResources(cls.tmp_directory)

    @classmethod
    def createResources(cls, directory):

        cls.txt_filename = os.path.join(directory, "test.txt")
        f = io.open(cls.txt_filename, "w+t")
        f.write(u"Kikoo")
        f.close()

        cls.missing_filename = os.path.join(directory, "test.missing")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp_directory)

    def test_missing_file(self):
        try:
            fabio.open(self.missing_filename)
            self.fail()
        except IOError:
            pass

    def test_wrong_file(self):
        try:
            fabio.open(self.txt_filename)
            self.fail()
        except IOError:
            pass


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestFailingFiles))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
