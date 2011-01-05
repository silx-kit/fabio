#!/usr/bin/env python
# -*- coding: utf8 -*- 

## Automatically adapted for numpy.oldnumeric Oct 05, 2007 by alter_code1.py



"""
# Unit tests

# builds on stuff from ImageD11.test.testpeaksearch
"""
import unittest, numpy as N, os
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
from fabio.edfimage import edfimage


MYHEADER = "{\n%-1020s}\n" % (
"""Omega = 0.0 ; 
Dim_1 = 256 ;
Dim_2 = 256 ;
DataType = FloatValue ;
ByteOrder = LowByteFirst ;
Image = 1;
History-1 = something=something else;
\n\n""")

MYIMAGE = N.ones((256, 256), N.float32) * 10
MYIMAGE[0, 0] = 0
MYIMAGE[1, 1] = 20

assert len(MYIMAGE[0:1, 0:1].tostring()) == 4, \
    len(MYIMAGE[0:1, 0:1].tostring())

class testflatedfs(unittest.TestCase):
    """ test some flat images """
    filename = "im0000.edf"

    def setUp(self):
        """ initialise"""
        outf = open(self.filename, "wb")
        assert len(MYHEADER) % 1024 == 0
        outf.write(MYHEADER)
        outf.write(MYIMAGE.tostring())
        outf.close()

    def tearDown(self):
        """ clean up """
        if os.path.exists(self.filename):
            os.remove(self.filename)

    def test_read(self):
        """ check readable"""
        obj = edfimage()
        obj.read(self.filename)
        self.assertEqual(obj.dim1 , 256)
        self.assertEqual(obj.dim2 , 256)
        self.assertEqual(obj.bpp , 4)
        self.assertEqual(obj.bytecode, N.float32)
        self.assertEqual(obj.data.shape, (256, 256))
        self.assertEqual(obj.header['History-1'],
                         "something=something else")

    def test_getstats(self):
        """ test statistics"""
        obj = edfimage()
        obj.read(self.filename)
        self.assertEqual(obj.getmean() , 10)
        self.assertEqual(obj.getmin() , 0)
        self.assertEqual(obj.getmax() , 20)

class testbzipedf(testflatedfs):
    """ same for bzipped versions """
    def setUp(self):
        """set it up"""
        testflatedfs.setUp(self)
        os.system("bzip2 %s" % (self.filename))
        self.filename += ".bz2"
        # self.filename will be the file to be removed

class testgzipedf(testflatedfs):
    """ same for gzipped versions """
    def setUp(self):
        """ set it up """
        testflatedfs.setUp(self)
        os.system("gzip %s" % (self.filename))
        self.filename += ".gz"
        # self.filename will be the file to be removed





# statistics come from fit2d I think
# filename dim1 dim2 min max mean stddev
TESTIMAGES = """F2K_Seb_Lyso0675.edf 2048 2048 982 17467 1504.3 217.61
F2K_Seb_Lyso0675.edf.bz2 2048 2048 982 17467 1504.3 217.61
F2K_Seb_Lyso0675.edf.gz 2048 2048 982 17467 1504.3 217.61"""


class testedfs(unittest.TestCase):
    """
    Read some test images on jon's disk
    FIXME: upload to sourceforge and add a setUp with wget?
    """
    def setUp(self):
        UtilsTest.getimage("F2K_Seb_Lyso0675.edf.bz2")


    def test_read(self):
        """ check we can read these images"""
        for line in TESTIMAGES.split("\n"):
            vals = line.split()
            name = vals[0]
            dim1, dim2 = [int(x) for x in vals[1:3]]
            mini, maxi, mean, stddev = [float(x) for x in vals[3:]]
            obj = edfimage()
            try:
                obj.read(os.path.join("testimages", name))
            except:
                print "Cannot read image", name
                raise
            self.assertAlmostEqual(mini, obj.getmin(), 2, "getmin")
            self.assertAlmostEqual(maxi, obj.getmax(), 2, "getmax")

            self.assertAlmostEqual(mean, obj.getmean(), 1, "getmean")
            self.assertAlmostEqual(stddev, obj.getstddev(), 2, "getstddev")
            self.assertEqual(dim1, obj.dim1, "dim1")
            self.assertEqual(dim2, obj.dim2, "dim2")

def test_suite_all_edf():
    testSuite = unittest.TestSuite()
    testSuite.addTest(testflatedfs("test_read"))
    testSuite.addTest(testflatedfs("test_getstats"))
    testSuite.addTest(testbzipedf("test_read"))
    testSuite.addTest(testbzipedf("test_getstats"))
    testSuite.addTest(testgzipedf("test_read"))
    testSuite.addTest(testgzipedf("test_getstats"))
    testSuite.addTest(testedfs("test_read"))
    return testSuite

if __name__ == '__main__':

    mysuite = test_suite_all_edf()
    runner = unittest.TextTestRunner()
    runner.run(mysuite)








