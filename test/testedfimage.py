#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
# Unit tests

# builds on stuff from ImageD11.test.testpeaksearch
"""
import unittest, sys, os, logging, tempfile
logger = logging.getLogger("testedfimage")
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
from fabio.edfimage import edfimage
import numpy
import gzip, bz2



class testflatedfs(unittest.TestCase):
    """ test some flat images """
    filename = os.path.join(UtilsTest.test_home, "testimages", "im0000.edf")
    MYHEADER = "{\n%-1020s}\n" % (
"""Omega = 0.0 ; 
Dim_1 = 256 ;
Dim_2 = 256 ;
DataType = FloatValue ;
ByteOrder = LowByteFirst ;
Image = 1;
History-1 = something=something else;
\n\n""")

    MYIMAGE = numpy.ones((256, 256), numpy.float32) * 10
    MYIMAGE[0, 0] = 0
    MYIMAGE[1, 1] = 20

    assert len(MYIMAGE[0:1, 0:1].tostring()) == 4, \
    len(MYIMAGE[0:1, 0:1].tostring())

    def setUp(self):
        """ initialize"""
        if not os.path.isfile(self.filename):
            outf = open(self.filename, "wb")
            assert len(self.MYHEADER) % 1024 == 0
            outf.write(self.MYHEADER)
            outf.write(self.MYIMAGE.tostring())
            outf.close()


    def test_read(self):
        """ check readable"""
        obj = edfimage()
        obj.read(self.filename)
        self.assertEqual(obj.dim1 , 256, msg="dim1!=256 for file: %s" % self.filename)
        self.assertEqual(obj.dim2 , 256, msg="dim2!=256 for file: %s" % self.filename)
        self.assertEqual(obj.bpp , 4, msg="bpp!=4 for file: %s" % self.filename)
        self.assertEqual(obj.bytecode, numpy.float32, msg="bytecode!=flot32 for file: %s" % self.filename)
        self.assertEqual(obj.data.shape, (256, 256), msg="shape!=(256,256) for file: %s" % self.filename)
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

class testgzipedf(testflatedfs):
    """ same for gzipped versions """
    def setUp(self):
        """ set it up """
        testflatedfs.setUp(self)
        if not os.path.isfile(self.filename + ".gz"):
                    gzip.open(self.filename + ".gz", "wb").write(open(self.filename, "rb").read())
        self.filename += ".gz"





# statistics come from fit2d I think
# filename dim1 dim2 min max mean stddev
TESTIMAGES = """F2K_Seb_Lyso0675.edf     2048 2048 982 17467 1504.29  217.61
                F2K_Seb_Lyso0675.edf.bz2 2048 2048 982 17467 1504.29  217.61
                F2K_Seb_Lyso0675.edf.gz  2048 2048 982 17467 1504.29  217.61
                id13_badPadding.edf      512  512  85  61947 275.62   583.44 """

class testedfs(unittest.TestCase):
    """
    Read some test images 
    """
    def setUp(self):
        self.im_dir = os.path.dirname(UtilsTest.getimage("F2K_Seb_Lyso0675.edf.bz2"))
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
                obj.read(os.path.join(self.im_dir, name))
            except:
                print "Cannot read image", name
                raise
            self.assertAlmostEqual(mini, obj.getmin(), 2, "testedfs: %s getmin()" % name)
            self.assertAlmostEqual(maxi, obj.getmax(), 2, "testedfs: %s getmax" % name)
            logger.info("%s Mean: exp=%s, obt=%s" % (name, mean, obj.getmean()))
            self.assertAlmostEqual(mean, obj.getmean(), 2, "testedfs: %s getmean" % name)
            logger.info("%s StdDev:  exp=%s, obt=%s" % (name, stddev, obj.getstddev()))
            self.assertAlmostEqual(stddev, obj.getstddev(), 2, "testedfs: %s getstddev" % name)
            self.assertEqual(dim1, obj.dim1, "testedfs: %s dim1" % name)
            self.assertEqual(dim2, obj.dim2, "testedfs: %s dim2" % name)

    def test_rebin(self):
        """test the rebin of edfdata"""
        f = edfimage()
        f.read(os.path.join(self.im_dir, "F2K_Seb_Lyso0675.edf"))
        f.rebin(1024, 1024)
        self.assertEqual(abs(numpy.array([[1547, 1439], [1536, 1494]]) - f.data).max(), 0, "data are the same after rebin")



class testedfcompresseddata(unittest.TestCase):
    """
    Read some test images with their data-block compressed.
    Z-Compression and Gzip compression are implemented Bzip2 and byte offet are experimental 
    """
    def setUp(self):
        self.im_dir = os.path.dirname(UtilsTest.getimage("edfGzip_U16.edf.bz2"))
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
            ref.read(os.path.join(self.im_dir, refFile))
        except:
            raise RuntimeError("Cannot read image Uncompressed image %s" % refFile)
        try:
            gzipped.read(os.path.join(self.im_dir, gzippedFile))
        except:
            raise RuntimeError("Cannot read image gzippedFile image %s" % gzippedFile)
        try:
            compressed.read(os.path.join(self.im_dir, compressedFile))
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
        self.multiFrameFilename = UtilsTest.getimage("MultiFrame.edf.bz2")[:-4]
        self.Frame0Filename = UtilsTest.getimage("MultiFrame-Frame0.edf.bz2")[:-4]
        self.Frame1Filename = UtilsTest.getimage("MultiFrame-Frame1.edf.bz2")[:-4]
        self.ref = edfimage()
        self.frame0 = edfimage()
        self.frame1 = edfimage()
        try:
            self.ref.read(self.multiFrameFilename)
        except:
            raise RuntimeError("Cannot read image multiFrameFilename image %s" % self.multiFrameFilename)
        try:
            self.frame0.read(self.Frame0Filename)
        except:
            raise RuntimeError("Cannot read image Frame0File image %s" % self.Frame0File)
        try:
            self.frame1.read(self.Frame1Filename)
        except:
            raise RuntimeError("Cannot read image Frame1File image %s" % self.Frame1File)

    def test_getFrame_multi(self):
        """testedfmultiframe.test_getFrame_multi"""
        self.assertEqual((self.ref.data - self.frame0.data).max(), 0, "getFrame_multi: Same data for frame 0")
        f1_multi = self.ref.getframe(1)
#        logger.warning("f1_multi.header=%s\nf1_multi.data=  %s" % (f1_multi.header, f1_multi.data))
        self.assertEqual((f1_multi.data - self.frame1.data).max(), 0, "getFrame_multi: Same data for frame 1")

    def test_getFrame_mono(self):
        "testedfmultiframe.test_getFrame_mono"
        self.assertEqual((self.ref.data - self.frame0.data).max(), 0, "getFrame_mono: Same data for frame 0")
        f1_mono = self.frame0.getframe(1)
        self.assertEqual((f1_mono.data - self.frame1.data).max(), 0, "getFrame_mono: Same data for frame 1")

    def test_next_multi(self):
        """testedfmultiframe.test_getFrame_mono"""
        self.assertEqual((self.ref.data - self.frame0.data).max(), 0, "next_multi: Same data for frame 0")
        next = self.ref.next()
        self.assertEqual((next.data - self.frame1.data).max(), 0, "next_multi: Same data for frame 1")

    def text_next_mono(self):
        "testedfmultiframe.text_next_mono"
        self.assertEqual((self.ref.data - self.frame0.data).max(), 0, "next_mono: Same data for frame 0")
        next = self.frame0.next()
        self.assertEqual((next.data - self.frame1.data).max(), 0, "next_mono: Same data for frame 1")

    def test_previous_multi(self):
        """testedfmultiframe.test_previous_multi"""
        f1 = self.ref.getframe(1)
        self.assertEqual((f1.data - self.frame1.data).max(), 0, "previous_multi: Same data for frame 1")
        f0 = f1.previous()
        self.assertEqual((f0.data - self.frame1.data).max(), 0, "previous_multi: Same data for frame 0")

    def test_previous_mono(self):
        "testedfmultiframe.test_previous_mono"
        f1 = self.ref.getframe(1)
        self.assertEqual((f1.data - self.frame1.data).max(), 0, "previous_mono: Same data for frame 1")
        prev = self.frame1.previous()
        self.assertEqual((prev.data - self.frame0.data).max(), 0, "previous_mono: Same data for frame 0")

    def  test_openimage_multiframes(self):
        "test if openimage can directly read first or second frame of a multi-frame"
        self.assertEqual((fabio.open(self.multiFrameFilename).data - self.frame0.data).max(), 0, "openimage_multiframes: Same data for default ")
        self.assertEqual((fabio.open(self.multiFrameFilename, 0).data - self.frame0.data).max(), 0, "openimage_multiframes: Same data for frame 0")
        self.assertEqual((fabio.open(self.multiFrameFilename, 1).data - self.frame1.data).max(), 0, "openimage_multiframes: Same data for frame 1")

class testedffastread(unittest.TestCase):
    """
    Read some test images with their data-block compressed.
    Z-Compression and Gzip compression are implemented Bzip2 and byte offet are experimental 
    """
    def setUp(self):
        self.refFilename = UtilsTest.getimage("MultiFrame-Frame0.edf.bz2")
        self.fastFilename = self.refFilename[:-4]
    def test_fastread(self):
        ref = fabio.open(self.refFilename)
        refdata = ref.data
        obt = ref.fastReadData(self.fastFilename)
        self.assertEqual(abs(obt - refdata).max(), 0, "testedffastread: Same data")

class testedfwrite(unittest.TestCase):
    """
    Write dummy edf files with various compression schemes
    
    """
    def setUp(self):
        self.data = numpy.arange(100).reshape((10, 10))
        self.header = {"toto": "tutu"}
        self.tmpdir = tempfile.mkdtemp(prefix="testedfwrite")
    def testFlat(self):
        self.filename = os.path.join(self.tmpdir, "merged.azim")
        e = edfimage(data=self.data, header=self.header)
        e.write(self.filename)
        r = fabio.open(self.filename)
        self.assert_(r.header["toto"] == self.header["toto"], "header are OK")
        self.assert_(abs(r.data - self.data).max() == 0, "data are OK")
        self.assertEqual(int(r.header["EDF_HeaderSize"]), 512, "header size is one 512 block")
    def testGzip(self):
        self.filename = os.path.join(self.tmpdir, "merged.azim.gz")
        e = edfimage(data=self.data, header=self.header)
        e.write(self.filename)
        r = fabio.open(self.filename)
        self.assert_(r.header["toto"] == self.header["toto"], "header are OK")
        self.assert_(abs(r.data - self.data).max() == 0, "data are OK")
        self.assertEqual(int(r.header["EDF_HeaderSize"]), 512, "header size is one 512 block")
    def testBzip2(self):
        self.filename = os.path.join(self.tmpdir, "merged.azim.gz")
        e = edfimage(data=self.data, header=self.header)
        e.write(self.filename)
        r = fabio.open(self.filename)
        self.assert_(r.header["toto"] == self.header["toto"], "header are OK")
        self.assert_(abs(r.data - self.data).max() == 0, "data are OK")
        self.assertEqual(int(r.header["EDF_HeaderSize"]), 512, "header size is one 512 block")
    def tearDown(self):
        os.unlink(self.filename)
        os.rmdir(self.tmpdir)

def test_suite_all_edf():
    testSuite = unittest.TestSuite()
    testSuite.addTest(testflatedfs("test_read"))
    testSuite.addTest(testflatedfs("test_getstats"))
    testSuite.addTest(testbzipedf("test_read"))
    testSuite.addTest(testbzipedf("test_getstats"))
    testSuite.addTest(testgzipedf("test_read"))
    testSuite.addTest(testgzipedf("test_getstats"))
    testSuite.addTest(testedfs("test_read"))
    testSuite.addTest(testedfs("test_rebin"))
    testSuite.addTest(testedfcompresseddata("test_read"))
    testSuite.addTest(testedfmultiframe("test_getFrame_multi"))
    testSuite.addTest(testedfmultiframe("test_getFrame_mono"))
    testSuite.addTest(testedfmultiframe("test_next_multi"))
    testSuite.addTest(testedfmultiframe("text_next_mono"))
    testSuite.addTest(testedfmultiframe("test_previous_multi"))
    testSuite.addTest(testedfmultiframe("test_openimage_multiframes"))
    testSuite.addTest(testedffastread("test_fastread"))
    testSuite.addTest(testedfwrite("testFlat"))
    testSuite.addTest(testedfwrite("testGzip"))
    testSuite.addTest(testedfwrite("testBzip2"))

    return testSuite

if __name__ == '__main__':
    mysuite = test_suite_all_edf()
    runner = unittest.TextTestRunner()
    runner.run(mysuite)
