#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test cases for the flat binary images

testsuite by Jerome Kieffer (Jerome.Kieffer@esrf.eu)
28/11/2014
"""
from __future__ import print_function, with_statement, division, absolute_import
import unittest
import sys
import os
import numpy
import gzip
import bz2

try:
    from .utilstest import UtilsTest
except (ValueError, SystemError):
    from utilstest import UtilsTest

logger = UtilsTest.get_logger(__file__)
fabio = sys.modules["fabio"]


class TestFlatBinary(unittest.TestCase):

    filenames = [os.path.join(UtilsTest.tempdir, i)
                 for i in ("not.a.file",
                           "bad_news_1234",
                           "empty_files_suck_1234.edf",
                           "notRUBY_1234.dat")]

    def setUp(self):
        for filename in self.filenames:
            f = open(filename, "wb")
            # A 2048 by 2048 blank image
            f.write("\0x0" * 2048 * 2048 * 2)
            f.close()

    def test_openimage(self):
        """
        test the opening of "junk" empty images ...
        JK: I wonder if this test makes sense !
        """
        nfail = 0
        for filename in self.filenames:
            try:
                im = fabio.open(filename)
                if im.data.tostring() != "\0x0" * 2048 * 2048 * 2:
                    nfail += 1
                else:
                    logger.info("**** Passed: %s" % filename)
            except:
                logger.warning("failed for: %s" % filename)
                nfail += 1
        self.assertEqual(nfail, 0, " %s failures out of %s" % (nfail, len(self.filenames)))

    def tearDown(self):
        for filename in self.filenames:
            os.remove(filename)


def test_suite_all_flat():
    testSuite = unittest.TestSuite()

#     testSuite.addTest(TestFlatBinary("test_openimage"))
    return testSuite

if __name__ == '__main__':
    mysuite = test_suite_all_flat()
    runner = unittest.TextTestRunner()
    runner.run(mysuite)
