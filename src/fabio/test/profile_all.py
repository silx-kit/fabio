#!/usr/bin/python
# coding: utf-8
#
#    Project: Azimuthal integration
#             https://github.com/pyFAI/pyFAI
#
#    Copyright (C) 2015 European Synchrotron Radiation Facility, Grenoble, France
#
#    Principal author:       Jérôme Kieffer (Jerome.Kieffer@ESRF.eu)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""Test suite for all pyFAI modules with timing and memory profiling"""

__authors__ = ["Jérôme Kieffer"]
__contact__ = "jerome.kieffer@esrf.eu"
__license__ = "MIT"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__date__ = "03/07/2024"

import sys
import unittest
import time

from . import test_all

import logging
profiler = logging.getLogger("memProf")
profiler.setLevel(logging.DEBUG)
profiler.handlers.append(logging.FileHandler("profile.log"))
logger = logging.getLogger(__name__)

WIN32_ERROR = "`profile_all` can only be used under UNIX, Windows is missing memory "

if sys.platform != "win32":
    import resource
else:
    logger.error(WIN32_ERROR)


class TestResult(unittest.TestResult):

    def startTest(self, test):
        if sys.platform == "win32":
            raise RuntimeError(WIN32_ERROR)
        self.__mem_start = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        self.__time_start = time.perf_counter()
        unittest.TestResult.startTest(self, test)

    def stopTest(self, test):
        unittest.TestResult.stopTest(self, test)
        if sys.platform == "win32":
            raise RuntimeError(WIN32_ERROR)
        mem = (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss - self.__mem_start) / 1e3
        profiler.info(f"Time: {time.perf_counter() - self.__time_start:.3f}s \t RAM: {mem:.3f}Mb\t{test.id()}")


class ProfileTestRunner(unittest.TextTestRunner):

    def _makeResult(self):
        return TestResult(stream=sys.stderr, descriptions=True, verbosity=1)


if __name__ == '__main__':
    suite = test_all.suite()
    runner = ProfileTestRunner()
    testresult = runner.run(suite)
    if testresult.wasSuccessful():
        # UtilsTest.clean_up()
        print("all tests passed")
    else:
        sys.exit(1)
