#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
#bruker Unit tests

#built on testedfimage
"""

import unittest, sys, os, logging, tempfile
logger = logging.getLogger("testbrukerimage")
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
from fabio.brukerimage import brukerimage
import numpy
import bz2, gzip
import tempfile
#this is actually a violation of the bruker format since the order of
# the header items is specified
#in the standard, whereas the order of a python dictionary is not
MYHEADER = {"FORMAT":'86',
            'NPIXELB':'2',
            'VERSION':'9',
            'HDRBLKS':'5',
            'NOVERFL':'4',
            'NCOLS':'256',
            'NROWS':'256',
            'WORDORD':'0'}

MYIMAGE = numpy.ones((256, 256), numpy.uint16) * 16
MYIMAGE[0, 0] = 0
MYIMAGE[1, 1] = 32
MYIMAGE[127:129, 127:129] = 65535

OVERFLOWS = [
    ["%09d" % 4194304, ("%07d" % (127 * 256 + 127))],
    ["%09d" % 4194304, ("%07d" % (127 * 256 + 128))],
    ["%09d" % 4194304, ("%07d" % (128 * 256 + 127))],
    ["%09d" % 4194304, ("%07d" % (128 * 256 + 128))]
    ]

class testbruker(unittest.TestCase):
    """basic test"""
    filename = os.path.join(UtilsTest.test_home, "testimages", "image.0000")

    def setUp(self):
        """ Generate a test bruker image """
        if not os.path.isfile(self.filename):
            fout = open(self.filename, 'wb')
            wrb = 0
            for key, val in MYHEADER.iteritems():
                fout.write(("%-7s" % key) + ':' + ("%-72s" % val))
                wrb = wrb + 80
            hdrblks = int(MYHEADER['HDRBLKS'])
            while (wrb < hdrblks * 512):
                fout.write("\x1a\x04")
                fout.write('.' * 78)
                wrb = wrb + 80
            fout.write(MYIMAGE.tostring())

            noverfl = int(MYHEADER['NOVERFL'])
            for ovf in OVERFLOWS:
                fout.write(ovf[0] + ovf[1])
            fout.write('.' * (512 - (16 * noverfl) % 512))

    def test_read(self):
        """ see if we can read the test image """
        obj = brukerimage()
        obj.read(self.filename)
        self.assertAlmostEqual(obj.getmean() , 272.0, 2)
        self.assertEqual(obj.getmin() , 0)
        self.assertEqual(obj.getmax() , 4194304)

class testbzipbruker(testbruker):
    """ test for a bzipped image """
    def setUp(self):
        """ create the image """
        testbruker.setUp(self)
        if not os.path.isfile(self.filename + ".bz2"):
            bz2.BZ2File(self.filename + ".bz2", "wb").write(open(self.filename, "rb").read())
            self.filename += ".bz2"

class testgzipbruker(testbruker):
    """ test for a gzipped image """
    def setUp(self):
        """ Create the image """
        testbruker.setUp(self)
        if not os.path.isfile(self.filename + ".gz"):
            gzip.open(self.filename + ".gz", "wb").write(open(self.filename, "rb").read())
#            os.system("gzip %s" % (self.filename))
            self.filename += ".gz"


class testbrukerLinear(unittest.TestCase):
    """basic test, test a random array of float32"""
    fd, filename = tempfile.mkstemp('0000', "bruker")
    os.close(fd)
    data = numpy.random.random((500, 550)).astype("float32")
    
    def test_linear(self):
        """ test for self consitency of random data read/write """
        obj = brukerimage(data=self.data)
        obj.write(self.filename)
        new = brukerimage()
        new.read(self.filename)
        error = abs(new.data - self.data).max()
        self.assert_(error < numpy.finfo(numpy.float32).eps, "Error is %s>1e-7" % error)


# statistics come from fit2d I think
# filename dim1 dim2 min max mean stddev

TESTIMAGES = """Cr8F8140k103.0026   512  512  0  145942 289.37  432.17 
                Cr8F8140k103.0026.gz   512  512  0  145942 289.37  432.17 
                Cr8F8140k103.0026.bz2   512  512  0 145942 289.37  432.17 """


class test_real_im(unittest.TestCase):
    """ check some read data from bruker detector"""
    def setUp(self):
        """
        download images
        """

        self.im_dir = os.path.dirname(UtilsTest.getimage("Cr8F8140k103.0026.bz2"))
        self.tempdir = tempfile.mkdtemp()

    def test_read(self):
        """ check we can read bruker images"""
        for line in TESTIMAGES.split("\n"):
            vals = line.split()
            name = vals[0]
            dim1, dim2 = [int(x) for x in vals[1:3]]
            mini, maxi, mean, stddev = [float(x) for x in vals[3:]]
            obj = brukerimage()
            obj.read(os.path.join(self.im_dir, name))
            self.assertAlmostEqual(mini, obj.getmin(), 2, "getmin")
            self.assertAlmostEqual(maxi, obj.getmax(), 2, "getmax")
            self.assertAlmostEqual(mean, obj.getmean(), 2, "getmean")
            self.assertAlmostEqual(stddev, obj.getstddev(), 2, "getstddev")
            self.assertEqual(dim1, obj.dim1, "dim1")
            self.assertEqual(dim2, obj.dim2, "dim2")

    def test_write(self):
        "Test writing with self consistency at the fabio level"
        for line in TESTIMAGES.split("\n"):
            vals = line.split()
            name = vals[0]
            obj = brukerimage()
            ref = brukerimage()
            fname = os.path.join(self.im_dir, name)
            obj.read(fname)
            obj.write(os.path.join(self.tempdir, name))
            other = brukerimage()
            other.read(os.path.join(self.tempdir, name))
            ref.read(fname)
            self.assertEqual(abs(obj.data - other.data).max(), 0, "data are the same")
            for key in ref.header:
                if key in ("filename",):
                    continue
                if key not in other.header:
                    logger.warning("Key %s is missing in new header, was %s" % (key, ref.header[key]))
                else:
                    self.assertEqual(ref.header[key], other.header[key], "value are the same for key %s: was %s now %s" % (key, ref.header[key], other.header[key]))

def test_suite_all_bruker():
    testSuite = unittest.TestSuite()
    testSuite.addTest(testbruker("test_read"))
    testSuite.addTest(testbzipbruker("test_read"))
    testSuite.addTest(testgzipbruker("test_read"))
    testSuite.addTest(test_real_im("test_read"))
    testSuite.addTest(test_real_im("test_write"))
    testSuite.addTest(testbrukerLinear("test_linear"))
    return testSuite

if __name__ == '__main__':
    mysuite = test_suite_all_bruker()
    runner = unittest.TextTestRunner()
    runner.run(mysuite)
