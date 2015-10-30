#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Project: Fable Input Output
#             https://github.com/kif/fabio
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
Test suite for all fabio modules.
"""
from __future__ import print_function, with_statement, division, absolute_import

import unittest
import sys
try:
    from . import utilstest
except (ValueError, SystemError):
    import utilstest

logger = utilstest.UtilsTest.get_logger(__file__)
fabio = sys.modules["fabio"]
if utilstest.IN_SOURCES:
    from testfabioimage import test_suite_all_fabio
    from testedfimage import test_suite_all_edf
    from testcbfimage import test_suite_all_cbf
    from testfilenames import test_suite_all_filenames
    from test_file_series import test_suite_all_series
    from test_filename_steps import test_suite_all_steps
    # from test_flat_binary       import test_suite_all_flat
    from testadscimage import test_suite_all_adsc
    from testfit2dmaskimage import test_suite_all_fit2d
    from testGEimage import test_suite_all_GE
    from testheadernotsingleton import test_suite_all_header
    from testmar345image import test_suite_all_mar345
    from testbrukerimage import test_suite_all_bruker
    from testbruker100image import test_suite_all_bruker100
    from testmccdimage import test_suite_all_mccd
    from testopenheader import test_suite_all_openheader
    from testopenimage import test_suite_all_openimage
    from testOXDimage import test_suite_all_OXD
    from testkcdimage import test_suite_all_kcd
    from testtifimage import test_suite_all_tiffimage
    from testXSDimage import test_suite_all_XSD
    from testraxisimage import test_suite_all_raxis
    from testpnmimage import test_suite_all_pnm
else:
    from .testfabioimage import test_suite_all_fabio
    from .testedfimage import test_suite_all_edf
    from .testcbfimage import test_suite_all_cbf
    from .testfilenames import test_suite_all_filenames
    from .test_file_series import test_suite_all_series
    from .test_filename_steps import test_suite_all_steps
    # from test_flat_binary       import test_suite_all_flat
    from .testadscimage import test_suite_all_adsc
    from .testfit2dmaskimage import test_suite_all_fit2d
    from .testGEimage import test_suite_all_GE
    from .testheadernotsingleton import test_suite_all_header
    from .testmar345image import test_suite_all_mar345
    from .testbrukerimage import test_suite_all_bruker
    from .testbruker100image import test_suite_all_bruker100
    from .testmccdimage import test_suite_all_mccd
    from .testopenheader import test_suite_all_openheader
    from .testopenimage import test_suite_all_openimage
    from .testOXDimage import test_suite_all_OXD
    from .testkcdimage import test_suite_all_kcd
    from .testtifimage import test_suite_all_tiffimage
    from .testXSDimage import test_suite_all_XSD
    from .testraxisimage import test_suite_all_raxis
    from .testpnmimage import test_suite_all_pnm


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

