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
# Unit tests
Jerome Kieffer, 04/12/2014
"""

import unittest
import logging

logger = logging.getLogger(__name__)

from fabio.openimage import openheader
from .utilstest import UtilsTest


class Test1(unittest.TestCase):
    """openheader opening edf"""

    def setUp(self):
        self.name = UtilsTest.getimage("F2K_Seb_Lyso0675_header_only.edf.bz2")[:-4]

    def testcase(self):
        """ check openheader can read edf headers"""
        for ext in ["", ".bz2", ".gz"]:
            name = self.name + ext
            obj = openheader(name)
            logger.debug(" %s obj = %s" % (name, obj.header))
            self.assertEqual(obj.header["title"],
                             "ESPIA FRELON Image",
                             "Error on file %s" % name)


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(Test1))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite)
