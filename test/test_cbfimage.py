#!/usr/bin/env python
# coding: utf8

"""

Unit tests for CBF images based on references images taken from:
http://pilatus.web.psi.ch/DATA/DATASETS/insulin_0.2/

"""

from fabio.openimage import openimage
from fabio.cbfimage import cbfimage
import unittest
import os, time
import logging
import sys

for idx, opts in enumerate(sys.argv[:]):
    if opts in ["-d", "--debug"]:
        logging.basicConfig(level=logging.INFO)
        sys.argv.pop(idx)
try:
    logging.debug("tests loaded from file: %s" % __file__)
except:
    __file__ = os.getcwd()

class test_cbfimage_reader(unittest.TestCase):
    """ test cbf image reader """
    def __init__(self, methodName):
        "Constructor of the class"
        unittest.TestCase.__init__(self, "runTest")
        testimgdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "testimages")
        self.edf_filename = os.path.join(testimgdir, "run2_1_00148.edf")
        self.cbf_filename = os.path.join(testimgdir, "run2_1_00148.cbf")

#    def setUp(self):
#        """ initialise"""
    def runTest(self):
        self.test_read()
        self.test_byte_offset()
#        pass   

    def test_read(self):
        """ check whole reader"""
        times = []
        times.append(time.time())
        cbf = openimage(self.cbf_filename)
        times.append(time.time())
        edf = openimage(self.edf_filename)
        times.append(time.time())

        self.assertAlmostEqual(0, (cbf.data - edf.data).max())
        logging.info("Reading CBF took %.3fs whereas the same EDF took %.3fs" % (times[1] - times[0], times[2] - times[1]))


    def test_byte_offset(self):
        """ check byte offset algorythm"""
        cbf = openimage(self.cbf_filename)
        starter = "\x0c\x1a\x04\xd5"
        startPos = cbf.cif["_array_data.data"].find(starter) + 4
        data = cbf.cif["_array_data.data"][ startPos: startPos + int(cbf.header["X-Binary-Size"])]

        startTime = time.time()
        numpyRes = cbfimage.analyseNumpy(data, size=cbf.dim1 * cbf.dim2)
        tNumpy = time.time() - startTime
        logging.info("Timing for Numpy method : %.3fs" % tNumpy)

        startTime = time.time()
        weaveRes = cbfimage.analyseWeave(data, size=cbf.dim1 * cbf.dim2)
        tWeave = time.time() - startTime
        delta = abs(numpyRes - weaveRes).max()
        self.assertAlmostEqual(0, delta)
        logging.info("Timing for Weave method : %.3fs, max delta=%s" % (tWeave, delta))

        startTime = time.time()
        pythonRes = cbfimage.analysePython(data, size=cbf.dim1 * cbf.dim2)
        tPython = time.time() - startTime
        delta = abs(numpyRes - pythonRes).max()
        self.assertAlmostEqual(0, delta)
        logging.info("Timing for Python method : %.3fs, max delta= %s" % (tPython, delta))

        from fabio.byte_offset import analyseCython
        startTime = time.time()
        cythonRes = analyseCython(stream=data, size=cbf.dim1 * cbf.dim2)
        tCython = time.time() - startTime
        delta = abs(numpyRes - cythonRes).max()
        self.assertAlmostEqual(0, delta)
        logging.info("Timing for Cython method : %.3fs, max delta= %s" % (tCython, delta))


if __name__ == "__main__":
    unittest.main()
