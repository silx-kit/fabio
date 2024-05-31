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
"""Unit tests for nexus file reader
"""

import unittest
import os
import logging

logger = logging.getLogger(__name__)

from .utilstest import UtilsTest
from .. import nexus
import numpy


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


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
