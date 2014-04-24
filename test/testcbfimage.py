#!/usr/bin/env python
# coding: utf-8

"""
2011: Jerome Kieffer for ESRF.

Unit tests for CBF images based on references images taken from:
http://pilatus.web.psi.ch/DATA/DATASETS/insulin_0.2/

"""
import unittest, sys, os, logging, tempfile
logger = logging.getLogger("testcbfimage")
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
from fabio.cbfimage import cbfimage
from fabio.compression import decByteOffet_numpy, decByteOffet_cython
import time

class test_cbfimage_reader(unittest.TestCase):
    """ test cbf image reader """

    def __init__(self, methodName):
        "Constructor of the class"
        unittest.TestCase.__init__(self, methodName)
        testimgdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "testimages")
        self.edf_filename = os.path.join(testimgdir, "run2_1_00148.edf")
        self.cbf_filename = os.path.join(testimgdir, "run2_1_00148.cbf")


    def setUp(self):
        """Download images"""

        UtilsTest.getimage(os.path.basename(self.edf_filename + ".bz2"))
        UtilsTest.getimage(os.path.basename(self.cbf_filename + ".bz2"))
        self.tempdir = tempfile.mkdtemp()
    def tearDown(self):
        UtilsTest.recursive_delete(self.tempdir)


    def test_read(self):
        """ check whole reader"""
        times = []
        times.append(time.time())
        cbf = fabio.open(self.cbf_filename)
        times.append(time.time())
        edf = fabio.open(self.edf_filename)
        times.append(time.time())

        self.assertAlmostEqual(0, abs(cbf.data - edf.data).max())
        logger.info("Reading CBF took %.3fs whereas the same EDF took %.3fs" % (times[1] - times[0], times[2] - times[1]))

    def test_write(self):
        "Rest writing with self consistency at the fabio level"
        name = os.path.basename(self.cbf_filename)
        obj = cbfimage()
        obj.read(self.cbf_filename)
        obj.write(os.path.join(self.tempdir, name))
        other = cbfimage()
        other.read(os.path.join(self.tempdir, name))
        self.assertEqual(abs(obj.data - other.data).max(), 0, "data are the same")
        for key in obj.header:
            if key in[ "filename", "X-Binary-Size-Padding"]:
                continue
            self.assertTrue(key in other.header, "Key %s is in header" % key)
            self.assertEqual(obj.header[key], other.header[key], "value are the same for key %s" % key)

    def test_byte_offset(self):
        """ check byte offset algorythm"""
        cbf = fabio.open(self.cbf_filename)
        starter = "\x0c\x1a\x04\xd5"
        startPos = cbf.cif["_array_data.data"].find(starter) + 4
        data = cbf.cif["_array_data.data"][ startPos: startPos + int(cbf.header["X-Binary-Size"])]
        startTime = time.time()
        numpyRes = decByteOffet_numpy(data, size=cbf.dim1 * cbf.dim2)
        tNumpy = time.time() - startTime
        logger.info("Timing for Numpy method : %.3fs" % tNumpy)

#        startTime = time.time()
#        weaveRes = cbfimage.analyseWeave(data, size=cbf.dim1 * cbf.dim2)
#        tWeave = time.time() - startTime
#        delta = abs(numpyRes - weaveRes).max()
#        self.assertAlmostEqual(0, delta)
#        logger.info("Timing for Weave method : %.3fs, max delta=%s" % (tWeave, delta))
#
#        startTime = time.time()
#        pythonRes = decByteOffet_numpy(data, size=cbf.dim1 * cbf.dim2)
#        tPython = time.time() - startTime
#        delta = abs(numpyRes - pythonRes).max()
#        self.assertAlmostEqual(0, delta)
#        logger.info("Timing for Python method : %.3fs, max delta= %s" % (tPython, delta))

        startTime = time.time()
        cythonRes = decByteOffet_cython(stream=data, size=cbf.dim1 * cbf.dim2)
        tCython = time.time() - startTime
        delta = abs(numpyRes - cythonRes).max()
        self.assertAlmostEqual(0, delta)
        logger.info("Timing for Cython method : %.3fs, max delta= %s" % (tCython, delta))

    def test_consitency_manual(self):
        """
        Test if an image can be read and saved and the results are "similar"
        """
        name = os.path.basename(self.cbf_filename)
        obj = fabio.open(self.cbf_filename)
        new = fabio.cbfimage.cbfimage(data=obj.data, header=obj.header)
        new.write(os.path.join(self.tempdir, name))
        other = fabio.open(os.path.join(self.tempdir, name))
        self.assertEqual(abs(obj.data - other.data).max(), 0, "data are the same")
        for key in obj.header:
            if key in[ "filename", "X-Binary-Size-Padding"]:
                continue
            self.assertTrue(key in other.header, "Key %s is in header" % key)
            self.assertEqual(obj.header[key], other.header[key], "value are the same for key %s [%s|%s]" % (key, obj.header[key], other.header[key]))

    def test_consitency_convert(self):
        """
        Test if an image can be read and saved and the results are "similar"
        """
        name = os.path.basename(self.cbf_filename)
        obj = fabio.open(self.cbf_filename)
        new = obj.convert("cbf")
        new.write(os.path.join(self.tempdir, name))
        other = fabio.open(os.path.join(self.tempdir, name))
        self.assertEqual(abs(obj.data - other.data).max(), 0, "data are the same")
        for key in obj.header:
            if key in[ "filename", "X-Binary-Size-Padding"]:
                continue
            self.assertTrue(key in other.header, "Key %s is in header" % key)
            self.assertEqual(obj.header[key], other.header[key], "value are the same for key %s [%s|%s]" % (key, obj.header[key], other.header[key]))

    def test_unicode(self):
        """
        Test if an image can be read and saved to an unicode named
        """
        name = unicode(os.path.basename(self.cbf_filename))
        obj = fabio.open(self.cbf_filename)
        obj.write(os.path.join(self.tempdir, name))
        other = fabio.open(os.path.join(self.tempdir, name))
        self.assertEqual(abs(obj.data - other.data).max(), 0, "data are the same")
        for key in obj.header:
            if key in[ "filename", "X-Binary-Size-Padding"]:
                continue
            self.assertTrue(key in other.header, "Key %s is in header" % key)
            self.assertEqual(obj.header[key], other.header[key], "value are the same for key %s [%s|%s]" % (key, obj.header[key], other.header[key]))


def test_suite_all_cbf():
    testSuite = unittest.TestSuite()
    testSuite.addTest(test_cbfimage_reader("test_read"))
    testSuite.addTest(test_cbfimage_reader("test_write"))
    testSuite.addTest(test_cbfimage_reader("test_byte_offset"))
    testSuite.addTest(test_cbfimage_reader("test_consitency_manual"))
    testSuite.addTest(test_cbfimage_reader("test_consitency_convert"))
    testSuite.addTest(test_cbfimage_reader("test_unicode"))

    return testSuite

if __name__ == '__main__':

    mysuite = test_suite_all_cbf()
    runner = unittest.TextTestRunner()
    runner.run(mysuite)

