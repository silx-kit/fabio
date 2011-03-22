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
import gzip, bz2

force_build = False


for idx, opts in enumerate(sys.argv[:]):
    if opts in ["-d", "--debug"]:
        logging.basicConfig(level=logging.DEBUG)
        sys.argv.pop(idx)
    elif opts in ["-f", "--force"]:
        force_build = True
        sys.argv.pop(sys.argv.index(opts))

try:
    logging.debug("tests loaded from file: %s" % __file__)
except:
    __file__ = os.getcwd()

from utilstest import UtilsTest

if force_build:
    UtilsTest.forceBuild()

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
    filename = "testimages/im0000.edf"

    def setUp(self):
        """ initialise"""
        if not os.path.isfile(self.filename):
            outf = open(self.filename, "wb")
            assert len(MYHEADER) % 1024 == 0
            outf.write(MYHEADER)
            outf.write(MYIMAGE.tostring())
            outf.close()

#    def tearDown(self):
#        """ clean up """
#        if os.path.exists(self.filename):
#            os.remove(self.filename)

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
        if not os.path.isfile(self.filename + ".bz2"):
                    bz2.BZ2File(self.filename + ".bz2", "wb").write(open(self.filename, "rb").read())
        self.filename += ".bz2"
        # self.filename will be the file to be removed

class testgzipedf(testflatedfs):
    """ same for gzipped versions """
    def setUp(self):
        """ set it up """
        testflatedfs.setUp(self)
        if not os.path.isfile(self.filename + ".gz"):
                    gzip.open(self.filename + ".gz", "wb").write(open(self.filename, "rb").read())
#        os.system("gzip %s" % (self.filename))
        self.filename += ".gz"
        # self.filename will be the file to be removed





# statistics come from fit2d I think
# filename dim1 dim2 min max mean stddev
TESTIMAGES = """F2K_Seb_Lyso0675.edf 2048 2048 982 17467 1504.3 217.61
F2K_Seb_Lyso0675.edf.bz2 2048 2048 982 17467 1504.3 217.61
F2K_Seb_Lyso0675.edf.gz 2048 2048 982 17467 1504.3 217.61
id13_badPadding.edf 512 512 85.0 61947.0 275.62 583.37 """

class testedfs(unittest.TestCase):
    """
    Read some test images 
    """
    def setUp(self):
        UtilsTest.getimage("F2K_Seb_Lyso0675.edf.bz2")
        UtilsTest.getimage("id13_badPadding.edf.bz2")

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
            self.assertAlmostEqual(mini, obj.getmin(), 2, "testedfs: %s getmin()" % name)
            self.assertAlmostEqual(maxi, obj.getmax(), 2, "testedfs: %s getmax" % name)
            self.assertAlmostEqual(mean, obj.getmean(), 1, "testedfs: %s getmean" % name)
            #There is a change in behavour in mean and std between python 2.6 and 2.7
            # python 2.7 does data.astype("float").std() whereas python2.6 works with int 
            logging.debug("StDev: exp=%s, obt=%s" % (stddev, obj.getstddev()))
            self.assertAlmostEqual(stddev, obj.getstddev(), 0, "testedfs: %s getstddev" % name)
            self.assertEqual(dim1, obj.dim1, "testedfs: %s dim1" % name)
            self.assertEqual(dim2, obj.dim2, "testedfs: %s dim2" % name)

class testedfcompresseddata(unittest.TestCase):
    """
    Read some test images with their data-block compressed.
    Z-Compression and Gzip compression are implemented Bzip2 and byte offet are experimental 
    """
    def setUp(self):
        UtilsTest.getimage("edfGzip_U16.edf.bz2")
        UtilsTest.getimage("edfCompressed_U16.edf.bz2")
        UtilsTest.getimage("edfUncompressed_U16.edf.bz2")

    def test_read(self):
        """ check we can read these images"""
        ref = edfimage()
        gzipped = edfimage()
        compressed = edfimage()
        refFile = "edfUncompressed_U16.edf"
        gzippedFile = "edfGzip_U16.edf"
        compressedFile = "edfCompressed_U16.edf"
        try:
            ref.read(os.path.join("testimages", refFile))
        except:
            raise RuntimeError("Cannot read image Uncompressed image %s" % refFile)
        try:
            gzipped.read(os.path.join("testimages", gzippedFile))
        except:
            raise RuntimeError("Cannot read image gzippedFile image %s" % gzippedFile)
        try:
            compressed.read(os.path.join("testimages", compressedFile))
        except:
            raise RuntimeError("Cannot read image compressedFile image %s" % compressedFile)
        self.assertEqual((ref.data - gzipped.data).max(), 0, "Gzipped data block is correct")
        self.assertEqual((ref.data - compressed.data).max(), 0, "Zlib compressed data block is correct")

class testedfmultiframe(unittest.TestCase):
    """
    Read some test images with their data-block compressed.
    Z-Compression and Gzip compression are implemented Bzip2 and byte offet are experimental 
    """
    def setUp(self):
        UtilsTest.getimage("MultiFrame.edf.bz2")
        UtilsTest.getimage("MultiFrame-Frame0.edf.bz2")
        UtilsTest.getimage("MultiFrame-Frame1.edf.bz2")

    def test_read(self):
        """ check we can read these images"""
        ref = edfimage()
        frame0 = edfimage()
        frame1 = edfimage()
        refFile = "MultiFrame.edf"
        Frame0File = "MultiFrame-Frame0.edf"
        Frame1File = "MultiFrame-Frame1.edf"
        try:
            ref.read(os.path.join("testimages", refFile))
        except:
            raise RuntimeError("Cannot read image refFile image %s" % refFile)
        try:
            frame0.read(os.path.join("testimages", Frame0File))
        except:
            raise RuntimeError("Cannot read image Frame0File image %s" % Frame0File)
        try:
            frame1.read(os.path.join("testimages", Frame1File))
        except:
            raise RuntimeError("Cannot read image Frame1File image %s" % Frame1File)

        self.assertEqual((ref.data - frame0.data).max(), 0, "Same data for frame 0")
        #self.assertEqual(ref.header, frame0.header, "same header for frame 0")
        ref.next()
        self.assertEqual((ref.data - frame1.data).max(), 0, "Same data for frame 1")
        #self.assertEqual(ref.header, frame1.header, "same header for frame 1")


def test_suite_all_edf():
    testSuite = unittest.TestSuite()
    testSuite.addTest(testflatedfs("test_read"))
    testSuite.addTest(testflatedfs("test_getstats"))
    testSuite.addTest(testbzipedf("test_read"))
    testSuite.addTest(testbzipedf("test_getstats"))
    testSuite.addTest(testgzipedf("test_read"))
    testSuite.addTest(testgzipedf("test_getstats"))
    testSuite.addTest(testedfs("test_read"))
    testSuite.addTest(testedfcompresseddata("test_read"))
    testSuite.addTest(testedfmultiframe("test_read"))
    return testSuite

if __name__ == '__main__':

    mysuite = test_suite_all_edf()
    runner = unittest.TextTestRunner()
    runner.run(mysuite)








