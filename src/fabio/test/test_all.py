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

import sys
import logging
import unittest

logger = logging.getLogger(__name__)

from . import test_fabio_image
from . import test_filenames
from . import test_file_series
from . import test_filename_steps
from . import test_header_not_singleton
from . import test_open_header
from . import test_open_image
from . import test_flat_binary
from . import test_compression
from . import test_nexus
from . import test_fabio_convert
from . import test_failing_files
from . import test_formats
from . import test_image_convert
from . import test_tiffio
from . import test_frames
from . import test_fabio
from . import codecs
from . import test_agi_bitfield
from . import test_densification
from . import test_io_limits
from . import test_utils_cli


def suite():
    testSuite = unittest.TestSuite()
    testSuite.addTest(test_fabio_image.suite())
    testSuite.addTest(test_filenames.suite())
    testSuite.addTest(test_file_series.suite())
    testSuite.addTest(test_filename_steps.suite())
    testSuite.addTest(test_header_not_singleton.suite())
    testSuite.addTest(test_open_header.suite())
    testSuite.addTest(test_open_image.suite())
    testSuite.addTest(test_flat_binary.suite())
    testSuite.addTest(test_compression.suite())
    testSuite.addTest(test_nexus.suite())
    testSuite.addTest(test_fabio_convert.suite())
    testSuite.addTest(test_failing_files.suite())
    testSuite.addTest(test_formats.suite())
    testSuite.addTest(test_image_convert.suite())
    testSuite.addTest(test_tiffio.suite())
    testSuite.addTest(test_frames.suite())
    testSuite.addTest(test_fabio.suite())
    testSuite.addTest(codecs.suite())
    testSuite.addTest(test_agi_bitfield.suite())
    testSuite.addTest(test_densification.suite())
    testSuite.addTest(test_io_limits.suite())
    testSuite.addTest(test_utils_cli.suite())
    return testSuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    if not runner.run(suite()).wasSuccessful():
        sys.exit(1)
