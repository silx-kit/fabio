#!/usr/bin/env python
# -*- coding: utf8 -*-

"""
Test suite for all fabio modules.
"""

import unittest
import os
import logging
import sys

for idx, opts in enumerate(sys.argv[:]):
    if opts in ["-d", "--debug"]:
        logging.basicConfig(level=logging.DEBUG)
        sys.argv.pop(idx)
try:
    logging.debug("tests loaded from file: %s" % __file__)
except:
    __file__ = os.getcwd()

from utilstest import UtilsTest


from testfabioimage import test_suite_all_fabio
from testedfimage import test_suite_all_edf
from testcbfimage import test_suite_all_cbf
from testfilenames import test_suite_all_filenames
from test_file_series import test_suite_all_series
from test_filename_steps import test_suite_all_steps
from test_flat_binary import test_suite_all_flat
from testadscimage import test_suite_all_adsc

def test_suite_all():
    testSuite = unittest.TestSuite()
    testSuite.addTest(test_suite_all_fabio())
    testSuite.addTest(test_suite_all_filenames())
    testSuite.addTest(test_suite_all_series())
    testSuite.addTest(test_suite_all_steps())
    testSuite.addTest(test_suite_all_flat())
    testSuite.addTest(test_suite_all_adsc())
    testSuite.addTest(test_suite_all_edf())
    testSuite.addTest(test_suite_all_cbf())
    return testSuite

if __name__ == '__main__':

    mysuite = test_suite_all()
    runner = unittest.TextTestRunner()
    runner.run(mysuite)

