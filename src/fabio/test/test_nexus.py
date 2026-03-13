#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Project: X-ray image reader
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
"""Unit tests for nexus file reader"""

import unittest
import os
import logging
from .utilstest import UtilsTest
from .. import nexus

logger = logging.getLogger(__name__)


class TestNexus(unittest.TestCase):
    def setUp(self):
        if nexus.h5py is None:
            self.skipTest("h5py library is not available. Skipping Nexus test")

    def test_nexus(self):
        "Test creation of Nexus files"
        fname = os.path.join(UtilsTest.tempdir, "nexus1.h5")
        nex = nexus.Nexus(fname)
        entry = nex.new_entry("entry")
        nex.new_instrument(entry, "ID00")
        nex.new_detector("camera")
        self.assertEqual(len(nex.get_entries()), 2, "nexus file has 2 entries")
        nex.close()
        self.assertTrue(os.path.exists(fname))
        os.unlink(fname)

    def test_from_time(self):
        fname = os.path.join(UtilsTest.tempdir, "nexus2.h5")
        nex = nexus.Nexus(fname)
        entry = nex.new_entry("entry")
        time1 = nexus.from_isotime(entry["start_time"][()])
        ltime = [str(entry["start_time"][()]).encode()]
        entry.create_dataset("bad_time", data=ltime)
        time2 = nexus.from_isotime(entry["bad_time"][()])
        self.assertEqual(time1, time2, "start_time in list does not works !")
        nex.close()
        self.assertTrue(os.path.exists(fname))
        os.unlink(fname)


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestNexus))
    return testsuite


if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite())
