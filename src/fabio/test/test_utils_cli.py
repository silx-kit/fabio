# coding: utf-8
#
#    Project: Azimuthal integration
#             https://github.com/silx-kit/pyFAI
#
#    Copyright (C) 2015-2025 European Synchrotron Radiation Facility, Grenoble, France
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

"""Test module for utils.shell module"""

__author__ = "valentin.valls@esrf.eu"
__license__ = "MIT"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__date__ = "19/06/2026"
__status__ = "development"
__docformat__ = "restructuredtext"

import unittest
import logging
from pathlib import Path
from .utilstest import UtilsTest
from ..utils.testutils import  LoggingCounter
from ..utils.cli import ProgressBar, expand_args
from .. import eigerimage
logger = logging.getLogger(__name__)


class TestUtilShell(unittest.TestCase):
    def test_coverage(self):
        """
        test function coverage
        """
        progressbar = ProgressBar("aaa", 15.1, 10)
        progressbar.update(1, "toto")
        progressbar.update(10.5, "toto")
        progressbar.update(20, "toto")
        progressbar.clear()

    def test_expand_args(self):
        _ = expand_args(["*.tif", "*.edf", "*.cbf", "*.img"])


class TestMisc(unittest.TestCase):

    def test_no_atleat_typo_in_source(self):
        # Locate the source file directly
        src_file = Path(eigerimage.__file__)
        self.assertTrue(src_file.exists(), f"Source file not found: {src_file}")
        content = src_file.read_text(encoding="utf-8")
        self.assertTrue("atleat_2d" not in content, "Typo 'atleat_2d' still present in eigerimage.py")


class TestCli(unittest.TestCase):
    def test_ulimit(self):
        import fabio.utils.cli
        with LoggingCounter(fabio.utils.cli._logger) as lc:
            fabio.utils.cli.relax_ulimit()
            counters = lc.counters

        try:
            import resource
        except Exception:
            return
        try:
            soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        except Exception as err:
            logger.error(f"{type(err)}: {err}")
        if counters.get(logging.warning) == 0:
            self.assertEqual(soft, hard, "soft limits have been increased to hard ones")
        else:
            logger.warning("Test skipped as `relax_ulimit` emitted warnings")


def suite():
    loader = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loader(TestUtilShell))
    testsuite.addTest(loader(TestMisc))
    testsuite.addTest(loader(TestCli))
    return testsuite


if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite())
    UtilsTest.clean_up()
