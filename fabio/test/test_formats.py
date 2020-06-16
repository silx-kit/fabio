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

# builds on stuff from ImageD11.test.testpeaksearch
28/11/2014
"""

import unittest
import logging

logger = logging.getLogger(__name__)
import fabio
from .. import fabioformats
from ..utils import deprecation
from ..utils import testutils


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
        self.assertRaises(RuntimeError, fabio.fabioimage.FabioImage.factory, "foobarimage")

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


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestRegistration))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
