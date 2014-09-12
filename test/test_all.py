#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test suite for all fabio modules.
"""

import unittest
import os
import logging
import sys

logger = logging.getLogger("test_all_fabio")
force_build = False

for opts in sys.argv[:]:
    if opts in ["-d", "--debug"]:
        logging.basicConfig(level=logging.DEBUG)
        sys.argv.pop(sys.argv.index(opts))
    elif opts in ["-i", "--info"]:
        logging.basicConfig(level=logging.INFO)
        sys.argv.pop(sys.argv.index(opts))
    elif opts in ["-f", "--force"]:
        force_build = True
        sys.argv.pop(sys.argv.index(opts))
try:
    logger.debug("Tests loaded from file: %s" % __file__)
except:
    __file__ = os.getcwd()

from utilstest import UtilsTest
if force_build:
    UtilsTest.forceBuild()
    import fabio


from testfabioimage import test_suite_all_fabio
from testedfimage import test_suite_all_edf
from testcbfimage import test_suite_all_cbf
from testfilenames import test_suite_all_filenames
from test_file_series import test_suite_all_series
from test_filename_steps import test_suite_all_steps
#from test_flat_binary       import test_suite_all_flat
from testadscimage import test_suite_all_adsc
from testfit2dmaskimage import test_suite_all_fit2d
from testGEimage import test_suite_all_GE
from testheadernotsingleton import test_suite_all_header
from testmar345image import test_suite_all_mar345
from testbrukerimage import test_suite_all_bruker
from testmccdimage import test_suite_all_mccd
from testopenheader import test_suite_all_openheader
from testopenimage import test_suite_all_openimage
from testOXDimage import test_suite_all_OXD
from testkcdimage import test_suite_all_kcd
from testtifimage import test_suite_all_tiffimage
from testXSDimage import test_suite_all_XSD
from testraxisimage import test_suite_all_raxis
from testpnmimage import test_suite_all_pnm


def test_suite_all():
    testSuite = unittest.TestSuite()
    testSuite.addTest(test_suite_all_fabio())
    testSuite.addTest(test_suite_all_filenames())
    testSuite.addTest(test_suite_all_series())
    testSuite.addTest(test_suite_all_steps())
#    testSuite.addTest(test_suite_all_flat())
    testSuite.addTest(test_suite_all_adsc())
    testSuite.addTest(test_suite_all_edf())
    testSuite.addTest(test_suite_all_cbf())
    testSuite.addTest(test_suite_all_fit2d())
    testSuite.addTest(test_suite_all_GE())
    testSuite.addTest(test_suite_all_header())
    testSuite.addTest(test_suite_all_mar345())
    testSuite.addTest(test_suite_all_bruker())
    testSuite.addTest(test_suite_all_mccd())
    testSuite.addTest(test_suite_all_openheader())
    testSuite.addTest(test_suite_all_openimage())
    testSuite.addTest(test_suite_all_OXD())
    testSuite.addTest(test_suite_all_kcd())
    testSuite.addTest(test_suite_all_tiffimage())
    testSuite.addTest(test_suite_all_XSD())
    testSuite.addTest(test_suite_all_raxis())
    testSuite.addTest(test_suite_all_pnm())
    return testSuite

if __name__ == '__main__':
    mysuite = test_suite_all()
    runner = unittest.TextTestRunner()
    if not runner.run(mysuite).wasSuccessful():
        sys.exit(1)

