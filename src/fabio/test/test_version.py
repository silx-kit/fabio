#
#    Project: X-ray image reader
#             https://github.com/silx-kit/fabio
#
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
"""Tests for the version handling (`fabio.version`)"""

import importlib
import unittest

# `fabio.version` the attribute is the version string, not the module
fabio_version = importlib.import_module("fabio.version")

calc_hexversion = fabio_version.calc_hexversion


class TestHexVersion(unittest.TestCase):
    @staticmethod
    def _expected_hexversion():
        """Version strings write a "dev" release as an alpha"""
        v = fabio_version
        level = "alpha" if v.RELEV == "dev" else v.RELEV
        return calc_hexversion(v.MAJOR, v.MINOR, v.MICRO, level, v.SERIAL)

    def test_documented_examples(self):
        """Examples given in the documentation of `fabio.version`"""
        self.assertEqual(calc_hexversion(2, 1, 0, "alpha", 3), 0x020100A3)
        self.assertEqual(calc_hexversion(1, 2, 3, "beta", 4), 0x010203B4)

    def test_release_levels_order(self):
        levels = ("dev", "alpha", "beta", "candidate", "final")
        values = [calc_hexversion(1, 2, 3, level) for level in levels]
        self.assertEqual(values, sorted(values))

    def test_string(self):
        """Parsing of version strings (regression: `_PATTERN` was not defined)"""
        self.assertEqual(calc_hexversion(string="1.2.3"), calc_hexversion(1, 2, 3, "final"))
        self.assertEqual(calc_hexversion(string="1.2.3a4"), calc_hexversion(1, 2, 3, "alpha", 4))
        self.assertEqual(calc_hexversion(string="1.2.3b4"), 0x010203B4)
        self.assertEqual(calc_hexversion(string="1.2.3rc1"), calc_hexversion(1, 2, 3, "candidate", 1))
        self.assertEqual(calc_hexversion(string=fabio_version.strictversion), self._expected_hexversion())

    def test_string_with_dash(self):
        """The `version` attribute is formatted like "1.2.3-beta4" or "1.2.3-a4"."""
        self.assertEqual(calc_hexversion(string="1.2.3-b4"), calc_hexversion(1, 2, 3, "beta", 4))
        self.assertEqual(calc_hexversion(string=fabio_version.version), self._expected_hexversion())

    def test_field_overflow(self):
        """Fields wider than their bits would silently corrupt the neighbouring field"""
        self.assertEqual(calc_hexversion(1, 255, 255, "final", 15), 0x1FFFFFF)
        for args in ((1, 256, 0), (1, 0, 256), (1, 0, 0, "alpha", 16)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                calc_hexversion(*args)
        with self.assertRaises(ValueError):
            calc_hexversion(string="1.256.0")

    def test_string_invalid(self):
        with self.assertRaises(ValueError):
            calc_hexversion(string="not a version")

    def test_string_order(self):
        strings = ["1.2.3a4", "1.2.3b4", "1.2.3rc1", "1.2.3"]
        values = [calc_hexversion(string=s) for s in strings]
        self.assertEqual(values, sorted(values))

    def test_year_as_major(self):
        """The major version is the year: `hexversion` goes beyond 32 bits but must stay monotonic"""
        versions = [(255, 255, 255, "final"), (2026, 6, 0, "final"), (2026, 10, 0, "dev"), (2026, 10, 0, "final"), (2027, 1, 0, "dev")]
        values = [calc_hexversion(*v) for v in versions]
        self.assertEqual(values, sorted(values))
        self.assertEqual(len(set(values)), len(values))


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestHexVersion))
    return testsuite


if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite())
