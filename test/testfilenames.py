#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
Test cases for filename deconstruction


testsuite by Jerome Kieffer (Jerome.Kieffer@esrf.eu)
28/11/2014
"""
from __future__ import print_function, with_statement, division, absolute_import
import unittest
import sys
import os

try:
    from .utilstest import UtilsTest
except (ValueError, SystemError):
    from utilstest import UtilsTest

logger = UtilsTest.get_logger(__file__)
fabio = sys.modules["fabio"]

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
    (3, 'tif', "data0003.tif"),
    (4, 'tif', "data0004.tiff"),
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
    (1     , 'adsc_or_OXD_or_HiPiC_or_raxis' , 'mb_LP_1_001.img'),
    (2     , 'adsc_or_OXD_or_HiPiC_or_raxis' , 'mb_LP_1_002.img.gz'),
    (3     , 'adsc_or_OXD_or_HiPiC_or_raxis' , 'mb_LP_1_003.img.bz2'),
    (3     , 'adsc_or_OXD_or_HiPiC_or_raxis' , os.path.join("data", 'mb_LP_1_003.img.bz2')),
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
            self.assertEqual(num, obj.num, name + " num=" + str(num) + \
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


def test_suite_all_filenames():
    testSuite = unittest.TestSuite()

    testSuite.addTest(TestFilenames("test_many_cases"))
    testSuite.addTest(TestFilenames("test_more_cases"))
    testSuite.addTest(TestFilenames("test_more_cases_jump"))

    return testSuite

if __name__ == '__main__':

    mysuite = test_suite_all_filenames()
    runner = unittest.TextTestRunner()
    runner.run(mysuite)
