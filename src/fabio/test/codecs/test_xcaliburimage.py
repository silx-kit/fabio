#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Project: Fable Input Output
#             https://github.com/silx-kit/fabio
#
#    Copyright (C) European Synchrotron Radiation Facility, Grenoble, France
#
#    Principal author:       Jérôme Kieffer (Jerome.Kieffer@ESRF.eu)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

"""
Unit tests for xcalibur struct used by crysalis to represent the mask

"""
__authors__ = ["Jérôme Kieffer"]
__contact__ = "jerome.kieffer@esrf.eu"
__license__ = "MIT"
__copyright__ = "2022 ESRF"
__date__ = "23/02/2023"

import unittest
import os
import time
import logging

logger = logging.getLogger(__name__)
import numpy
import fabio
from fabio.xcaliburimage import CcdCharacteristiscs, XcaliburImage
from ..utilstest import UtilsTest


class TestCcdCharacteristiscs(unittest.TestCase):
    """ test CcdCharacteristiscs struct reader """
    @classmethod
    def setUpClass(cls)->None:
        cls.ccdfiles = [UtilsTest.getimage(i) for i in ("scan0001.ccd", "scan0005.ccd", "scan0050.ccd", "scan0059.ccd", "scan0066.ccd")]
    @classmethod
    def tearDownClass(cls)->None:
        cls.ccfiles = None 
    def test_parse(self):
        for afile in self.ccdfiles:
            ref = CcdCharacteristiscs.read(afile)
            obt = CcdCharacteristiscs.loads(ref.dumps())
            for key in CcdCharacteristiscs.__dataclass_fields__:
                for what in (ref, obt):
                    if what.__getattribute__(key) == tuple():
                        what.__setattr__(key, [])
            self.assertEqual(ref, obt, f"{afile} matches ")
    
class testXcalibureImage(unittest.TestCase):
    @classmethod
    def setUpClass(cls)->None:
        cls.filename = UtilsTest.getimage("Pilatus1M.cbf")
    @classmethod
    def tearDownClass(cls)->None:
        cls.filename = None 
    def test_decomposition(self):
        ref = (fabio.open(self.filename).data<0).astype("int8")
        xcal = XcaliburImage(data=ref)
        try:
            import pyFAI.ext.dynamic_rectangle
        except ImportError:
            logger.warning("PyFAI not available: only a coarse description of the mask is provided")
            precise = False
        else:
            precise = True

        ccd = xcal.decompose(full=True)
        obt = ccd.build_mask(ref.shape)
        if precise:
            self.assertTrue(numpy.allclose(ref, obt), "mask is the same")        

    
def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestCcdCharacteristiscs))
    testsuite.addTest(loadTests(testXcalibureImage))    
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
      
        