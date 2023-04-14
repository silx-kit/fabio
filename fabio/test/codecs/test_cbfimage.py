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
2011: Jerome Kieffer for ESRF.

Unit tests for CBF images based on references images taken from:
http://pilatus.web.psi.ch/DATA/DATASETS/insulin_0.2/

19/01/2015
"""

import unittest
import os
import time
import logging

logger = logging.getLogger(__name__)
import numpy
import fabio
from fabio.cbfimage import CbfImage, CIF
from fabio.compression import decByteOffset_numpy, decByteOffset_cython
from ..utilstest import UtilsTest
from ..testutils import LoggingValidator


class TestCbfReader(unittest.TestCase):
    """ test cbf image reader """

    def setUp(self):
        """Download images"""
        self.edf_filename = "run2_1_00148.edf.bz2"
        self.edf_filename = UtilsTest.getimage(self.edf_filename)[:-4]
        self.cbf_filename = "run2_1_00148.cbf.bz2"
        self.cbf_filename = UtilsTest.getimage(self.cbf_filename)[:-4]

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
        obj = CbfImage()
        obj.read(self.cbf_filename)
        obj.write(os.path.join(UtilsTest.tempdir, name))
        other = CbfImage()
        other.read(os.path.join(UtilsTest.tempdir, name))
        self.assertEqual(abs(obj.data - other.data).max(), 0, "data are the same")
        for key in obj.header:
            if key in["filename", "X-Binary-Size-Padding"]:
                continue
            self.assertTrue(key in other.header, "Key %s is in header" % key)
            self.assertEqual(obj.header[key], other.header[key], "value are the same for key %s" % key)
        # By destroying the object, one actually closes the file, which is needed under windows.
        del obj
        del other
        if os.path.exists(os.path.join(UtilsTest.tempdir, name)):
            os.unlink(os.path.join(UtilsTest.tempdir, name))

    def test_byte_offset(self):
        """ check byte offset algorithm"""
        cbf = fabio.open(self.cbf_filename)
        starter = b"\x0c\x1a\x04\xd5"
        cbs = cbf.cbs
        startPos = cbs.find(starter) + 4
        data = cbs[startPos: startPos + int(cbf.header["X-Binary-Size"])]
        startTime = time.time()
        size = cbf.shape[0] * cbf.shape[1]
        numpyRes = decByteOffset_numpy(data, size=size)
        tNumpy = time.time() - startTime
        logger.info("Timing for Numpy method : %.3fs" % tNumpy)

        startTime = time.time()
        cythonRes = decByteOffset_cython(stream=data, size=size)
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
        new = CbfImage(data=obj.data, header=obj.header)
        new.write(os.path.join(UtilsTest.tempdir, name))
        other = fabio.open(os.path.join(UtilsTest.tempdir, name))
        self.assertEqual(abs(obj.data - other.data).max(), 0, "data are the same")
        for key in obj.header:
            if key in["filename", "X-Binary-Size-Padding"]:
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
        new.write(os.path.join(UtilsTest.tempdir, name))
        other = fabio.open(os.path.join(UtilsTest.tempdir, name))
        self.assertEqual(abs(obj.data - other.data).max(), 0, "data are the same")
        for key in obj.header:
            if key in["filename", "X-Binary-Size-Padding"]:
                continue
            self.assertTrue(key in other.header, "Key %s is in header" % key)
            self.assertEqual(obj.header[key], other.header[key], "value are the same for key %s [%s|%s]" % (key, obj.header[key], other.header[key]))

    def test_unicode(self):
        """
        Test if an image can be read and saved to an unicode named
        """
        name = u"%s" % os.path.basename(self.cbf_filename)
        obj = fabio.open(self.cbf_filename)
        obj.write(os.path.join(UtilsTest.tempdir, name))
        other = fabio.open(os.path.join(UtilsTest.tempdir, name))
        self.assertEqual(abs(obj.data - other.data).max(), 0, "data are the same")
        for key in obj.header:
            if key in["filename", "X-Binary-Size-Padding"]:
                continue
            self.assertTrue(key in other.header, "Key %s is in header" % key)
            self.assertEqual(obj.header[key], other.header[key], "value are the same for key %s [%s|%s]" % (key, obj.header[key], other.header[key]))

    def test_bug_388(self):
        data = numpy.random.randint(0, 100, size=(27, 31)).astype(numpy.int32)
        im = CbfImage(data=data, header={})
        filename = os.path.join(UtilsTest.tempdir, "bad_name.edf")
        im.write(filename)
        res = fabio.open(filename)
        self.assertEqual(abs(data - res.data).max(), 0, "Data are the same despite the wrong name")

    def test_bug_408(self):
        "Bug when reading files generated by XDS"
        xds_filename = UtilsTest.getimage("XDS.cbf.bz2")[:-4]
        _ = fabio.open(xds_filename)

    def test_bug_528(self):
        "Bug when writing/reading small files"
        filename = os.path.join(UtilsTest.tempdir, "bug528.cbf")
        data = numpy.array([[1, 2, 3]])
        CbfImage(header={}, data=data).write(filename)
        with LoggingValidator(fabio.cbfimage.logger, error=0, warning=0):
            fimg = fabio.open(filename)
        self.assertEqual(abs(data - fimg.data).max(), 0, "data match")

    def test_cif(self):
        LaB6 = """
data_global
_amcsd_formula_title 'B6La'
loop_
_publ_author_name
'Eliseev A'
'Efremmov V'
'Kuzmicheva G'
'Konovalova E'
'Lazorenko V'
'Paderno Y'
'Khlyustova S'
_journal_name_full 'Kristallografiya'
_journal_volume 31 
_journal_year 1986
_journal_page_first 803
_journal_page_last 805
_publ_section_title
;
 X-ray structural investigation of single crystals of lanthanum, cerium,
 and samarium hexaborides
 _cod_database_code 1000057
;
_database_code_amcsd 0014189
_chemical_formula_sum 'La B6'
_chemical_formula_sum ''
_cell_length_a 4.1570
_cell_length_b 4.1570
_cell_length_c 4.1570
_cell_angle_alpha 90
_cell_angle_beta 90
_cell_angle_gamma 90
_cell_volume 71.836
_exptl_crystal_density_diffrn      4.710
_symmetry_space_group_name_H-M 'P m 3 m'
loop_
_space_group_symop_operation_xyz
  'x,y,z'
  'z,-x,y'
  '-y,z,-x'
  'x,-y,z'
  '-z,x,-y'
  'y,-z,x'
  '-x,y,-z'
  'x,-z,-y'
  '-z,y,x'
  'y,-x,-z'
  '-x,z,y'
  'z,-y,-x'
  '-y,x,z'
  'x,z,y'
  '-z,-y,-x'
  'y,x,z'
  '-x,-z,-y'
  'z,y,x'
  '-y,-x,-z'
  'z,x,-y'
  '-y,-z,x'
  'x,y,-z'
  '-z,-x,y'
  'y,z,-x'
  '-x,-y,z'
  '-z,x,y'
  'y,-z,-x'
  '-x,y,z'
  'z,-x,-y'
  '-y,z,x'
  'x,-y,-z'
  '-x,z,-y'
  'z,-y,x'
  '-y,x,-z'
  'x,-z,y'
  '-z,y,-x'
  'y,-x,z'
  '-x,-z,y'
  'z,y,-x'
  '-y,-x,z'
  'x,z,-y'
  '-z,-y,x'
  'y,x,-z'
  '-z,-x,-y'
  'y,z,x'
  '-x,-y,-z'
  'z,x,y'
  '-y,-z,-x'
loop_
_atom_site_label
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
La   0.00000   0.00000   0.00000
B   0.19750   0.50000   0.50000
"""
        filename = os.path.join(UtilsTest.tempdir, "LaB6.cif")
        filename2 = os.path.join(UtilsTest.tempdir, "LaB6_2.cif")
        # print(filename, filename2)
        with open(filename, "w") as w:
            w.write(LaB6)
        lab6 = CIF(filename)
        # print(lab6)
        lab6.saveCIF(filename2)
        lab62 = CIF(filename2)
        self.assertEqual(len(lab6), len(lab62), "size matches")


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestCbfReader))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
