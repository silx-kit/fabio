#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
# Unit tests

Updated by Jerome Kieffer (jerome.kieffer@esrf.eu), 2011
"""

import unittest, sys, os, logging
logger = logging.getLogger("testcompression")
force_build = False

for opts in sys.argv[:]:
    if opts in ["-d", "--debug"]:
        logging.basicConfig(level=logging.DEBUG)
        sys.argv.pop(sys.argv.index(opts))
    elif opts in ["-i", "--info"]:
        logging.basicConfig(level=logging.INFO)
        sys.argv.pop(sys.argv.index(opts))
    elif opts in ["-f", "--force"]:
        force_build = True
        sys.argv.pop(sys.argv.index(opts))
try:
    logger.debug("Tests loaded from file: %s" % __file__)
except:
    __file__ = os.getcwd()

from utilstest import UtilsTest
if force_build:
    UtilsTest.forceBuild()
import fabio
import fabio.compression as compression
import numpy


class testbyteoffset(unittest.TestCase):
    """ 
    test the byte offset compression and decompression 
    """
    def setUp(self):
        self.ds = numpy.array([0, 1, 2, 127, 0, 1, 2, 128, 0, 1, 2, 32767, 0, 1, 2, 32768, 0, 1, 2, 2147483647, 0, 1, 2, 2147483648, 0, 1, 2, 128, 129, 130, 32767, 32768, 128, 129, 130, 32768, 2147483647, 2147483648])
        self.ref = '\x00\x01\x01}\x81\x01\x01~\x80\x80\xff\x01\x01\x80\xfd\x7f\x80\x01\x80\x01\x01\x80\xfe\x7f\x80\x00\x80\x00\x80\xff\xff\x01\x01\x80\x00\x80\xfd\xff\xff\x7f\x80\x00\x80\x01\x00\x00\x80\x01\x01\x80\x00\x80\xfe\xff\xff\x7f\x80\x00\x80\x00\x00\x00\x80\x00\x00\x00\x80\xff\xff\xff\xff\x01\x01~\x01\x01\x80}\x7f\x01\x80\x80\x80\x01\x01\x80~\x7f\x80\x00\x80\xff\x7f\xff\x7f\x01'
    def testComp(self):
        """
        """
        ds = numpy.array([0, 128])
        ref = "\x00\x80\x80\00"
        self.assertEqual(ref, compression.compByteOffet_numpy(ds) , "test +128")
        ds = numpy.array([0, -128])
        ref = '\x00\x80\x80\xff'
        self.assertEqual(ref, compression.compByteOffet_numpy(ds) , "test -128")
        ds = numpy.array([10, -128])
        ref = '\n\x80v\xff'
        self.assertEqual(ref, compression.compByteOffet_numpy(ds) , "test +10 -128")
        self.assertEqual(self.ref, compression.compByteOffet_numpy(self.ds) , "test larger")

    def testSC(self):
        """test that datasets are unchanged after various comression/decompressions"""

        obt_np = compression.decByteOffet_numpy(compression.compByteOffet_numpy(self.ds))
        self.assertEqual(abs(self.ds - obt_np).max(), 0.0, "numpy algo")
        obt_cy = compression.decByteOffet_cython(compression.compByteOffet_numpy(self.ds))
        self.assertEqual(abs(self.ds - obt_cy).max(), 0.0, "cython algo")
        obt_cy2 = compression.decByteOffet_cython(compression.compByteOffet_numpy(self.ds), self.ds.size)
        self.assertEqual(abs(self.ds - obt_cy2).max(), 0.0, "cython algo_orig")
        obt_we = compression.decByteOffet_weave(compression.compByteOffet_numpy(self.ds), self.ds.size)
        self.assertEqual(abs(self.ds - obt_we).max(), 0.0, "weave algo")





def test_suite_all_compression():
    testSuite = unittest.TestSuite()
    testSuite.addTest(testbyteoffset("testSC"))
    testSuite.addTest(testbyteoffset("testSC"))
    return testSuite

if __name__ == '__main__':
    mysuite = test_suite_all_compression()
    runner = unittest.TextTestRunner()
    runner.run(mysuite)



