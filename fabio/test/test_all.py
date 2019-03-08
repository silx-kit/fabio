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

"""Test suite for all fabio modules."""
from __future__ import print_function, with_statement, division, absolute_import

import sys
import logging
import unittest

logger = logging.getLogger(__name__)

from . import testfabioimage
from . import testfilenames
from . import test_file_series
from . import test_filename_steps
from . import testheadernotsingleton
from . import testopenheader
from . import testopenimage
from . import test_flat_binary
from . import testcompression
from . import test_nexus
from . import testfabioconvert
from . import test_failing_files
from . import test_formats
from . import test_image_convert
from . import test_tiffio
from . import test_frames
from . import test_fabio
from . import codecs


def suite():
    testSuite = unittest.TestSuite()
    testSuite.addTest(testfabioimage.suite())
    testSuite.addTest(testfilenames.suite())
    testSuite.addTest(test_file_series.suite())
    testSuite.addTest(test_filename_steps.suite())
    testSuite.addTest(testheadernotsingleton.suite())
    testSuite.addTest(testopenheader.suite())
    testSuite.addTest(testopenimage.suite())
    testSuite.addTest(test_flat_binary.suite())
    testSuite.addTest(testcompression.suite())
    testSuite.addTest(test_nexus.suite())
    testSuite.addTest(testfabioconvert.suite())
    testSuite.addTest(test_failing_files.suite())
    testSuite.addTest(test_formats.suite())
    testSuite.addTest(test_image_convert.suite())
    testSuite.addTest(test_tiffio.suite())
    testSuite.addTest(test_frames.suite())
    testSuite.addTest(test_fabio.suite())
    testSuite.addTest(codecs.suite())
    return testSuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    if not runner.run(suite()).wasSuccessful():
        sys.exit(1)
