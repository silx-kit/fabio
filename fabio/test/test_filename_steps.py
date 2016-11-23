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
Test cases for the Next/Previous ...

28/11/2014
"""
from __future__ import print_function, with_statement, division, absolute_import
import unittest
import sys
import os
if __name__ == '__main__':
    import pkgutil
    __path__ = pkgutil.extend_path([os.path.dirname(__file__)], "fabio.test")
from .utilstest import UtilsTest

logger = UtilsTest.get_logger(__file__)
fabio = sys.modules["fabio"]


class TestNext(unittest.TestCase):
    def test_next1(self):
        for name, next_ in [["data0001.edf", "data0002.edf"],
                ["bob1.edf", "bob2.edf"],
                ["1.edf", "2.edf"],
                ["1.mar2300", "2.mar2300"],
                ]:
            self.assertEqual(next_, fabio.next_filename(name))


class TestPrev(unittest.TestCase):
    def test_prev1(self):
        for name, prev in [["data0001.edf", "data0000.edf"],
                ["bob1.edf", "bob0.edf"],
                ["1.edf", "0.edf" ],
                ["1.mar2300", "0.mar2300" ],
                ]:
            self.assertEqual(prev, fabio.previous_filename(name))


class TestJump(unittest.TestCase):
    def test_jump1(self):
        for name, res, num in [["data0001.edf", "data99993.edf", 99993],
                ["bob1.edf", "bob0.edf", 0],
                ["1.edf", "123456.edf", 123456],
                ["mydata001.mar2300.gz", "mydata003.mar2300.gz", 3 ],
                ]:
            self.assertEqual(res, fabio.jump_filename(name, num))


def suite():
    testsuite = unittest.TestSuite()

    testsuite.addTest(TestNext("test_next1"))
    testsuite.addTest(TestPrev("test_prev1"))
    testsuite.addTest(TestJump("test_jump1"))
    return testsuite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
