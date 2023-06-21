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
Test cases for filename deconstruction


testsuite by Jerome Kieffer (Jerome.Kieffer@esrf.eu)
28/11/2014
"""

import unittest
import os
import logging
import tempfile


logger = logging.getLogger(__name__)

import fabio
import numpy

CASES = [
    (1, 'edf', "data0001.edf"),
    (10001, 'edf', "data10001.edf"),
    (10001, 'edf', "data10001.edf.gz"),
    (10001, 'edf', "data10001.edf.bz2"),
    (2, 'marccd', "data0002.mccd"),
    (12345, 'marccd', "data12345.mccd"),
    (10001, 'marccd', "data10001.mccd.gz"),
    (10001, 'marccd', "data10001.mccd.bz2"),
    (123, 'marccd', "data123.mccd.gz"),
    (3, 'tif_or_pilatus', "data0003.tif"),
    (4, 'tif_or_pilatus', "data0004.tiff"),
    (12, 'bruker', "sucrose101.012.gz"),
    (99, 'bruker', "sucrose101.099"),
    (99, 'bruker', "sucrose101.0099"),
    (99, 'bruker', "sucrose101.0099.bz2"),
    (99, 'bruker', "sucrose101.0099.gz"),
    (2, 'fit2dmask', "fit2d.msk"),
    (None, 'fit2dmask', "mymask.msk"),
    (670005, 'edf', 'S82P670005.edf'),
    (670005, 'edf', 'S82P670005.edf.gz'),
    # based on only the name it can be either img or oxd
    (1, 'dtrek_or_oxd_or_hipic_or_raxis', 'mb_LP_1_001.img'),
    (2, 'dtrek_or_oxd_or_hipic_or_raxis', 'mb_LP_1_002.img.gz'),
    (3, 'dtrek_or_oxd_or_hipic_or_raxis', 'mb_LP_1_003.img.bz2'),
    (3, 'dtrek_or_oxd_or_hipic_or_raxis', os.path.join("data", 'mb_LP_1_003.img.bz2')),
]

MORE_CASES = [
    ("data0010.edf", "data0012.edf", 10),
    ("data1000.pnm", "data999.pnm", 1000),
    ("data0999.pnm", "data1000.pnm", 999),
    ("data123457.edf", "data123456.edf", 123457),
    ("d0ata000100.mccd", "d0ata000012.mccd", 100),
    (os.path.join("images/sampledir", "P33S670003.edf"),
     os.path.join("images/sampledir", "P33S670002.edf"), 670003),
    (os.path.join("images/P33S67", "P33S670003.edf"),
     os.path.join("images/P33S67", "P33S670002.edf"), 670003),
    ("image2301.mar2300", "image2300.mar2300", 2301),
    ("image2300.mar2300", "image2301.mar2300", 2300),
    ("image.0123", "image.1234", 123),
    ("mymask.msk", "mymask.msk", None),
    ("data_123.mccd.bz2", "data_001.mccd.bz2", 123)
]


class TestFilenames(unittest.TestCase):
    """ check the name -> number, type conversions """

    def test_many_cases(self):
        """ loop over CASES """
        for num, typ, name in CASES:
            obj = fabio.FilenameObject(filename=name)
            self.assertEqual(num, obj.num, name + " num=" + str(num) +
                             " != obj.num=" + str(obj.num))
            self.assertEqual(typ, "_or_".join(obj.format),
                             name + " " + "_or_".join(obj.format))
            self.assertEqual(name, obj.tostring(), name + " " + obj.tostring())

    def test_more_cases(self):
        for nname, oname, num in MORE_CASES:
            name = fabio.construct_filename(oname, num)
            self.assertEqual(name, nname)

    def test_more_cases_jump(self):
        for nname, oname, num in MORE_CASES:
            name = fabio.jump_filename(oname, num)
            self.assertEqual(name, nname)


class TestFilenameObjects(unittest.TestCase):

    def setUp(self):
        """ make a small test dataset """
        self.datashape = (10,11)
        self.nframes = 5
        self.tempdir = tempfile.mkdtemp()
        self.fnames = [os.path.join(self.tempdir, "FNO%04d.edf" % iframe)
                       for iframe in range(self.nframes)]
        data = numpy.zeros(self.datashape,numpy.uint16)
        im = fabio.edfimage.edfimage(data)
        for iframe, fname in enumerate(self.fnames):
            im.header["checkthing"] = str(iframe)
            im.write(fname)

    def tearDown(self):
        for name in self.fnames:
            os.remove(name)
        os.rmdir(self.tempdir)

    def test_files_are_being_opened(self):
        """Regression test for Fable"""
        for iframe, fname in enumerate(self.fnames):
            obj = fabio.FilenameObject(filename=fname)
            # read via the FilenameObject
            o1  = fabio.open(obj)
            self.assertEqual(o1.data.shape, self.datashape)
            self.assertEqual(o1.header['checkthing'], str(iframe))
            # And via the tostring
            o2  = fabio.open(obj.tostring())
            self.assertEqual(o2.data.shape, self.datashape)
            self.assertEqual(o2.header['checkthing'], str(iframe))

    def test_FileNameObject_can_iterate(self):
        """Regression test for Fable"""
        obj = fabio.FilenameObject(filename=self.fnames[0])
        for iframe, fname in enumerate(self.fnames):
            obj.num = iframe
            # read via the FilenameObject
            o1  = fabio.open(obj)
            self.assertEqual(o1.data.shape, self.datashape)
            self.assertEqual(o1.header['checkthing'], str(iframe))
            # And via the tostring
            o2  = fabio.open(obj.tostring())
            self.assertEqual(o2.data.shape, self.datashape)
            self.assertEqual(o2.header['checkthing'], str(iframe))
            # And the real name
            o3  = fabio.open(fname)
            self.assertEqual(o3.data.shape, self.datashape)
            self.assertEqual(o3.header['checkthing'], str(iframe))


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestFilenames))
    testsuite.addTest(loadTests(TestFilenameObjects))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
