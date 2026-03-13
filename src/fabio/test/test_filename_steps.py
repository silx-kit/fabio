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
Test cases for the Next/Previous ...

28/11/2014
"""

import unittest
import logging
import fabio

logger = logging.getLogger(__name__)


class TestNext(unittest.TestCase):
    def test_next1(self):
        files = [
            ["data0001.edf", "data0002.edf"],
            ["bob1.edf", "bob2.edf"],
            ["1.edf", "2.edf"],
            ["1.mar2300", "2.mar2300"],
        ]
        for name, next_ in files:
            self.assertEqual(next_, fabio.next_filename(name))


class TestPrev(unittest.TestCase):
    def test_prev1(self):
        files = [
            ["data0001.edf", "data0000.edf"],
            ["bob1.edf", "bob0.edf"],
            ["1.edf", "0.edf"],
            ["1.mar2300", "0.mar2300"],
        ]
        for name, prev in files:
            self.assertEqual(prev, fabio.previous_filename(name))


class TestJump(unittest.TestCase):
    def test_jump1(self):
        files = [
            ["data0001.edf", "data99993.edf", 99993],
            ["bob1.edf", "bob0.edf", 0],
            ["1.edf", "123456.edf", 123456],
            ["mydata001.mar2300.gz", "mydata003.mar2300.gz", 3],
        ]
        for name, res, num in files:
            self.assertEqual(res, fabio.jump_filename(name, num))


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestNext))
    testsuite.addTest(loadTests(TestPrev))
    testsuite.addTest(loadTests(TestJump))
    return testsuite


if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite())
