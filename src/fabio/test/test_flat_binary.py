# coding: utf-8
#
#    Project: X-ray image reader
#             https://github.com/silx-kit/fabio
#
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
"""
Test cases for the flat binary images

testsuite by Jerome Kieffer (Jerome.Kieffer@esrf.eu)
28/11/2014
"""

import unittest
import os
import logging
from .utilstest import UtilsTest
import fabio

logger = logging.getLogger(__name__)


class TestFlatBinary(unittest.TestCase):
    filenames = [
        os.path.join(UtilsTest.tempdir, i)
        for i in (
            "not.a.file",
            "bad_news_1234",
            "empty_files_suck_1234.edf",
            "notRUBY_1234.dat",
        )
    ]

    def setUp(self):
        for filename in self.filenames:
            with open(filename, "wb") as f:
                # A 2048 by 2048 blank image
                f.write(b"\x00" * (2048 * 2048 * 2 + 8192))

    def test_openimage(self):
        """
        test the opening of "junk" empty images ...
        JK: I doubt if this test makes sense !
        """
        nfail = 0
        for filename in self.filenames:
            try:
                im = fabio.open(filename)
            except Exception as err:
                logger.warning("failed for: %s. \n%s: %s",filename, type(err), err)
                nfail += 1
            else:
                if im.data.tobytes() == b"\x00" * (2048 * 2048 * 2 + 8192):
                    nfail += 1
                else:
                    logger.info("**** Passed: %s" % filename)

        self.assertEqual(
            nfail, 0, f"{nfail} failures out of {len(self.filenames)}"
        )

    def tearDown(self):
        for filename in self.filenames:
            os.remove(filename)


def suite():
    # loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    # testsuite.addTest(loadTests(TestFlatBinary))
    return testsuite


if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite())
