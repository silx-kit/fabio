#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test cases for the Next/Previous ...

28/11/2014
"""
from __future__ import print_function, with_statement, division, absolute_import
import unittest
import sys

try:
    from .utilstest import UtilsTest
except (ValueError, SystemError):
    from utilstest import UtilsTest

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


def test_suite_all_steps():
    testSuite = unittest.TestSuite()

    testSuite.addTest(TestNext("test_next1"))
    testSuite.addTest(TestPrev("test_prev1"))
    testSuite.addTest(TestJump("test_jump1"))
    return testSuite

if __name__ == '__main__':
    mysuite = test_suite_all_steps()
    runner = unittest.TextTestRunner()
    runner.run(mysuite)
