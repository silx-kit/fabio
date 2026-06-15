# coding: utf-8
#
#    Project: X-ray image reader
#             https://github.com/silx-kit/fabio
#
#
#    Copyright (C) European Synchrotron Radiation Facility, Grenoble, France
#
#    Principal author:       Jérôme Kieffer (Jerome.Kieffer@ESRF.eu)
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#  .
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#  .
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.

"""
Test module for each codecs supported by FabIO
"""

__authors__ = ["Jérôme Kieffer"]
__contact__ = "jerome.kieffer@esrf.eu"
__license__ = "MIT+"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__date__ = "15/06/2026"


import unittest


def suite():
    from . import test_edfimage
    from . import test_edfimage_expg
    from . import test_cbfimage
    from . import test_dtrekimage
    from . import test_fit2dmaskimage
    from . import test_fit2dspreadsheetimage
    from . import test_geimage
    from . import test_mar345image
    from . import test_brukerimage
    from . import test_bruker100image
    from . import test_mccdimage
    from . import test_oxdimage
    from . import test_kcdimage
    from . import test_tifimage
    from . import test_xsdimage
    from . import test_raxisimage
    from . import test_pnmimage
    from . import test_numpyimage
    from . import test_pilatusimage
    from . import test_eigerimage
    from . import test_lambdaimage
    from . import test_hdf5image
    from . import test_fit2dimage
    from . import test_speimage
    from . import test_jpegimage
    from . import test_jpeg2kimage
    from . import test_mpaimage
    from . import test_dm3image
    from . import test_mrcimage
    from . import test_pixiimage
    from . import test_esperantoimage
    from . import test_limaimage
    from . import test_hipicimage
    from . import test_binaryimage
    from . import test_xcaliburimage

    testSuite = unittest.TestSuite()
    testSuite.addTest(test_edfimage.suite())
    testSuite.addTest(test_edfimage_expg.suite())
    testSuite.addTest(test_cbfimage.suite())
    testSuite.addTest(test_dtrekimage.suite())
    testSuite.addTest(test_fit2dmaskimage.suite())
    testSuite.addTest(test_fit2dspreadsheetimage.suite())
    testSuite.addTest(test_geimage.suite())
    testSuite.addTest(test_mar345image.suite())
    testSuite.addTest(test_brukerimage.suite())
    testSuite.addTest(test_bruker100image.suite())
    testSuite.addTest(test_mccdimage.suite())
    testSuite.addTest(test_oxdimage.suite())
    testSuite.addTest(test_kcdimage.suite())
    testSuite.addTest(test_tifimage.suite())
    testSuite.addTest(test_xsdimage.suite())
    testSuite.addTest(test_raxisimage.suite())
    testSuite.addTest(test_pnmimage.suite())
    testSuite.addTest(test_numpyimage.suite())
    testSuite.addTest(test_pilatusimage.suite())
    testSuite.addTest(test_eigerimage.suite())
    testSuite.addTest(test_hdf5image.suite())
    testSuite.addTest(test_fit2dimage.suite())
    testSuite.addTest(test_speimage.suite())
    testSuite.addTest(test_jpegimage.suite())
    testSuite.addTest(test_jpeg2kimage.suite())
    testSuite.addTest(test_mpaimage.suite())
    testSuite.addTest(test_dm3image.suite())
    testSuite.addTest(test_mrcimage.suite())
    testSuite.addTest(test_pixiimage.suite())
    testSuite.addTest(test_esperantoimage.suite())
    testSuite.addTest(test_limaimage.suite())
    testSuite.addTest(test_hipicimage.suite())
    testSuite.addTest(test_binaryimage.suite())
    testSuite.addTest(test_xcaliburimage.suite())
    testSuite.addTest(test_lambdaimage.suite())
    return testSuite


def run_tests():
    """Run test complete test_suite"""
    runner = unittest.TextTestRunner()
    if not runner.run(suite()).wasSuccessful():
        print("Test suite failed")
        return 1
    else:
        print("Test suite succeeded")
        return 0
