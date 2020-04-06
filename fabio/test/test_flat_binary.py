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
Test cases for the flat binary images

testsuite by Jerome Kieffer (Jerome.Kieffer@esrf.eu)
28/11/2014
"""
import unittest
import os
import logging

from .utilstest import UtilsTest

logger = logging.getLogger(__name__)
import fabio


class TestFlatBinary(unittest.TestCase):

    filenames = [os.path.join(UtilsTest.tempdir, i)
                 for i in ("not.a.file",
                           "bad_news_1234",
                           "empty_files_suck_1234.edf",
                           "notRUBY_1234.dat")]

    def setUp(self):
        for filename in self.filenames:
            with open(filename, "wb") as f:
                # A 2048 by 2048 blank image
                f.write("\0x0" * 2048 * 2048 * 2)

    def test_openimage(self):
        """
        test the opening of "junk" empty images ...
        JK: I wonder if this test makes sense !
        """
        nfail = 0
        for filename in self.filenames:
            try:
                im = fabio.open(filename)
                if im.data.tobytes() != "\0x0" * 2048 * 2048 * 2:
                    nfail += 1
                else:
                    logger.info("**** Passed: %s" % filename)
            except Exception:
                logger.warning("failed for: %s" % filename)
                nfail += 1
        self.assertEqual(nfail, 0, " %s failures out of %s" % (nfail, len(self.filenames)))

    def tearDown(self):
        for filename in self.filenames:
            os.remove(filename)


def suite():
    # loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    # testsuite.addTest(loadTests(TestFlatBinary))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
