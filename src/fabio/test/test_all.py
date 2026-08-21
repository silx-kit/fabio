#!/usr/bin/env python
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

"""Test suite for all fabio modules."""

import logging
import sys
import unittest

from . import (
    codecs,
    test_agi_bitfield,
    test_compression,
    test_densification,
    test_fabio,
    test_fabio_convert,
    test_fabio_image,
    test_failing_files,
    test_file_series,
    test_filename_steps,
    test_filenames,
    test_flat_binary,
    test_formats,
    test_frames,
    test_header_not_singleton,
    test_image_convert,
    test_import,
    test_io_limits,
    test_nexus,
    test_open_header,
    test_open_image,
    test_tiffio,
    test_utils_cli,
)

logger = logging.getLogger(__name__)


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
    testSuite.addTest(test_import.suite())
    return testSuite


if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    if not runner.run(suite()).wasSuccessful():
        sys.exit(1)
