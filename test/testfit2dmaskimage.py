#!/usr/bin/env python
# -*- coding: utf8 -*-
## Automatically adapted for numpy.oldnumeric Oct 05, 2007 by alter_code1.py



# Unit tests

""" Test the fit2d mask reader

Updated by Jerome Kieffer (jerome.kieffer@esrf.eu), 2011
"""
import unittest, os
import numpy as N
import logging
import sys

for idx, opts in enumerate(sys.argv[:]):
    if opts in ["-d", "--debug"]:
        logging.basicConfig(level=logging.DEBUG)
        sys.argv.pop(idx)
try:
    logging.debug("tests loaded from file: %s" % __file__)
except:
    __file__ = os.getcwd()

from utilstest import UtilsTest



from fabio.fit2dmaskimage import fit2dmaskimage
from fabio.edfimage import edfimage

class testfacemask(unittest.TestCase):
    """ test the picture of a face """
    filename = "testimages/face.msk"
    edffilename = "testimages/face.edf.gz"

    def setUp(self):
        """
        download images
        """
        UtilsTest.getimage("face.msk.bz2")
        UtilsTest.getimage("face.edf.bz2")


    def test_getmatch(self):
        """ test edf and msk are the same """
        i = fit2dmaskimage()
        i.read(self.filename)
        j = edfimage()
        j.read(self.edffilename)
        # print "edf: dim1",oe.dim1,"dim2",oe.dim2
        self.assertEqual(i.dim1, j.dim1)
        self.assertEqual(i.dim2, j.dim2)
        self.assertEqual(i.data.shape, j.data.shape)
        diff = j.data - i.data
        sumd = N.sum(N.ravel(N.absolute(diff)).astype(N.float32))
        self.assertEqual(sumd , 0)

class testclickedmask(unittest.TestCase):
    """ A few random clicks to make a test mask """
    filename = "testimages/fit2d_click.msk"
    edffilename = "testimages/fit2d_click.edf.gz"

    def setUp(self):
        """
        download images
        """
        UtilsTest.getimage("fit2d_click.msk.bz2")
        UtilsTest.getimage("fit2d_click.edf.bz2")

    def test_read(self):
        """ Check it reads a mask OK """
        i = fit2dmaskimage()
        i.read(self.filename)
        self.assertEqual(i.dim1 , 1024)
        self.assertEqual(i.dim2 , 1024)
        self.assertEqual(i.bpp , 1)
        self.assertEqual(i.bytecode, N.uint8)
        self.assertEqual(i.data.shape, (1024, 1024))

    def test_getmatch(self):
        """ test edf and msk are the same """
        i = fit2dmaskimage()
        j = edfimage()
        i.read(self.filename)
        j.read(self.edffilename)
        self.assertEqual(i.data.shape, j.data.shape)
        diff = j.data - i.data
        self.assertEqual(i.getmax(), 1)
        self.assertEqual(i.getmin(), 0)
        sumd = N.sum(N.ravel(diff).astype(N.float32))
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



