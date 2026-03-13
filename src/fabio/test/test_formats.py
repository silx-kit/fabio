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
# Unit tests

# builds on stuff from ImageD11.test.testpeaksearch
28/11/2014
"""

import unittest
import logging
import fabio
from .. import fabioformats
from ..utils import deprecation
from ..utils import testutils

logger = logging.getLogger(__name__)


class TestRegistration(unittest.TestCase):
    def test_fabio_factory(self):
        image = fabio.factory("edfimage")
        self.assertIsNotNone(image)

    def test_fabio_factory_missing_format(self):
        self.assertRaises(RuntimeError, fabio.factory, "foobarimage")

    def test_fabioformats_factory(self):
        image = fabioformats.factory("edfimage")
        self.assertIsNotNone(image)

    def test_fabioformats_factory_missing_format(self):
        self.assertRaises(RuntimeError, fabioformats.factory, "foobarimage")

    @testutils.test_logging(deprecation.depreclog, warning=1)
    def test_deprecated_fabioimage_factory(self):
        """Check that it is still working"""
        image = fabio.fabioimage.FabioImage.factory("edfimage")
        self.assertIsNotNone(image)

    @testutils.test_logging(deprecation.depreclog, warning=1)
    def test_deprecated_fabioimage_factory_missing_format(self):
        """Check that it is still working"""
        self.assertRaises(
            RuntimeError, fabio.fabioimage.FabioImage.factory, "foobarimage"
        )

    def test_not_existing(self):
        self.assertIsNone(fabioformats.get_class_by_name("myformat0"))

    def test_annotation(self):
        @fabio.register
        class MyFormat1(fabio.fabioimage.FabioImage):
            pass

        self.assertIsNotNone(fabioformats.get_class_by_name("myformat1"))

    def test_function(self):
        class MyFormat2(fabio.fabioimage.FabioImage):
            pass

        fabio.register(MyFormat2)
        self.assertIsNotNone(fabioformats.get_class_by_name("myformat2"))

    def test_extenstion_registry(self):
        for ext in fabioformats._get_extension_mapping():
            self.assertFalse("." in ext)


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestRegistration))
    return testsuite


if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite())
