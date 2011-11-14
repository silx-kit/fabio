#!/usr/bin/env python
# -*- coding: utf8 -*-
## Automatically adapted for numpy.oldnumeric Oct 05, 2007 by alter_code1.py



# Unit tests

""" Test the fit2d mask reader

Updated by Jerome Kieffer (jerome.kieffer@esrf.eu), 2011
"""
import unittest, sys, os, logging
logger = logging.getLogger("testfit2dmaskdfimage")
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
from fabio.fit2dmaskimage import fit2dmaskimage
import numpy

class testfacemask(unittest.TestCase):
    """ test the picture of a face """

    def setUp(self):
        """
        download images
        """
        self.filename = UtilsTest.getimage("face.msk.bz2")[:-4]
        self.edffilename = UtilsTest.getimage("face.edf.bz2") [:-4]


    def test_getmatch(self):
        """ test edf and msk are the same """
        i = fit2dmaskimage()
        i.read(self.filename)
        j = fabio.open(self.edffilename)
        # print "edf: dim1",oe.dim1,"dim2",oe.dim2
        self.assertEqual(i.dim1, j.dim1)
        self.assertEqual(i.dim2, j.dim2)
        self.assertEqual(i.data.shape, j.data.shape)
        diff = j.data - i.data
        sumd = abs(diff).sum(dtype=float)
        self.assertEqual(sumd , 0.0)

class testclickedmask(unittest.TestCase):
    """ A few random clicks to make a test mask """

    def setUp(self):
        """
        download images
        """
        self.filename = UtilsTest.getimage("fit2d_click.msk.bz2")[:-4]
        self.edffilename = UtilsTest.getimage("fit2d_click.edf.bz2")[:-4]

    def test_read(self):
        """ Check it reads a mask OK """
        i = fit2dmaskimage()
        i.read(self.filename)
        self.assertEqual(i.dim1 , 1024)
        self.assertEqual(i.dim2 , 1024)
        self.assertEqual(i.bpp , 1)
        self.assertEqual(i.bytecode, numpy.uint8)
        self.assertEqual(i.data.shape, (1024, 1024))

    def test_getmatch(self):
        """ test edf and msk are the same """
        i = fit2dmaskimage()
        j = fabio.open(self.edffilename)
        i.read(self.filename)
        self.assertEqual(i.data.shape, j.data.shape)
        diff = j.data - i.data
        self.assertEqual(i.getmax(), 1)
        self.assertEqual(i.getmin(), 0)
        sumd = abs(diff).sum(dtype=float)
        self.assertEqual(sumd , 0)





def test_suite_all_fit2d():
    testSuite = unittest.TestSuite()
    testSuite.addTest(testfacemask("test_getmatch"))
    testSuite.addTest(testclickedmask("test_read"))
    testSuite.addTest(testclickedmask("test_getmatch"))
    return testSuite

if __name__ == '__main__':
    mysuite = test_suite_all_fit2d()
    runner = unittest.TextTestRunner()
    runner.run(mysuite)



