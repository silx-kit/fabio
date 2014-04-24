#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# Unit tests for raxis images
"""
import unittest, sys, os, logging, tempfile
logger = logging.getLogger("testraxisimage")
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
from fabio.raxisimage import raxisimage

# filename dim1 dim2 min max mean stddev
TESTIMAGES = """mgzn-20hpt.img     2300 1280 16 15040  287.82 570.72
                mgzn-20hpt.img.bz2 2300 1280 16 15040  287.82 570.72
                mgzn-20hpt.img.gz  2300 1280 16 15040  287.82 570.72"""
#                Seek from end is not supported with gzip


class testRaxisImage(unittest.TestCase):
    def setUp(self):
        """
        download images
        """
        self.mar = UtilsTest.getimage("mgzn-20hpt.img.bz2")[:-4]
        self.tempdir = tempfile.mkdtemp()
    def tearDown(self):
        UtilsTest.recursive_delete(self.tempdir)

    def test_read(self):
        """
        Test the reading of Mar345 images
        """
        for line in TESTIMAGES.split('\n'):
            vals = line.strip().split()
            name = vals[0]
            logger.debug("Testing file %s" % name)
            dim1, dim2 = [int(x) for x in vals[1:3]]
            mini, maxi, mean, stddev = [float(x) for x in vals[3:]]
            obj = raxisimage()
            obj.read(os.path.join(os.path.dirname(self.mar), name))

            self.assertAlmostEqual(mini, obj.getmin(), 2, "getmin [%s,%s]" % (mini, obj.getmin()))
            self.assertAlmostEqual(maxi, obj.getmax(), 2, "getmax [%s,%s]" % (maxi, obj.getmax()))
            self.assertAlmostEqual(mean, obj.getmean(), 2, "getmean [%s,%s]" % (mean, obj.getmean()))
            self.assertAlmostEqual(stddev, obj.getstddev(), 2, "getstddev [%s,%s]" % (stddev, obj.getstddev()))
            self.assertEqual(dim1, obj.dim1, "dim1")
            self.assertEqual(dim2, obj.dim2, "dim2")
#            self.assertEqual(obj.dim1, obj.dim2, "dim2!=dim1")
    def test_write(self):
        "Test writing with self consistency at the fabio level"
        for line in TESTIMAGES.split("\n"):
            logger.debug("Processing file: %s" % line)
            vals = line.split()
            name = vals[0]
            obj = raxisimage()
            obj.read(os.path.join(os.path.dirname(self.mar), name))
            obj.write(os.path.join(self.tempdir, name))
            other = raxisimage()
            other.read(os.path.join(self.tempdir, name))
            self.assertEqual(abs(obj.data - other.data).max(), 0, "data are the same")
            for key in obj.header:
                if key == "filename":
                    continue
                self.assertTrue(key in other.header, "Key %s is in header" % key)
                self.assertEqual(obj.header[key], other.header[key], "value are the same for key %s: [%s|%s]" % (key, obj.header[key], other.header[key]))

    def test_memoryleak(self):
        """
        This test takes a lot of time, so only in debug mode.
        """
        if logger.getEffectiveLevel() <= logging.INFO:
            logger.debug("Testing for memory leak")
            for i in range(1000):
                img = fabio.open(self.mar)
                print i



def test_suite_all_raxis():
    testSuite = unittest.TestSuite()
    testSuite.addTest(testRaxisImage("test_read"))
#    testSuite.addTest(testRaxisImage("test_write"))
#    testSuite.addTest(testRaxisImage("test_memoryleak"))

    return testSuite

if __name__ == '__main__':
    mysuite = test_suite_all_raxis()
    runner = unittest.TextTestRunner()
    runner.run(mysuite)
