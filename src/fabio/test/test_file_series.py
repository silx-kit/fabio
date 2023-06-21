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
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""
test cases for fileseries

28/11/2014
"""

import unittest
import logging
import os
import shutil
import numpy

logger = logging.getLogger(__name__)

import fabio
from fabio.file_series import numbered_file_series, file_series, filename_series
from fabio.file_series import FileSeries
from .utilstest import UtilsTest


class TestRandomSeries(unittest.TestCase):
    """arbitrary series"""

    def setUp(self):
        """sets up"""
        self.fso = file_series(["first", "second", "last"])

    def testfirst(self):
        """check first"""
        self.assertEqual("first", self.fso.first())

    def testlast(self):
        """check first"""
        self.assertEqual("last", self.fso.last())

    def testjump(self):
        """check jump"""
        self.assertEqual("second", self.fso.jump(1))


class TestEdfNumbered(unittest.TestCase):
    """
    Typical sequence of edf files
    """

    def setUp(self):
        """ note extension has the . in it"""
        self.fso = numbered_file_series("mydata", 0, 10005, ".edf")

    def testfirst(self):
        """ first in series"""
        self.assertEqual(self.fso.first(), "mydata0000.edf")

    def testlast(self):
        """ last in series"""
        self.assertEqual(self.fso.last(), "mydata10005.edf")

    def testnext(self):
        """ check all in order """
        mylist = ["mydata%04d.edf" % (i) for i in range(0, 10005)]
        i = 1
        while i < len(mylist):
            self.assertEqual(mylist[i], self.fso.next())
            i += 1

    def testprevious(self):
        """ check all in order """
        mylist = ["mydata%04d.edf" % (i) for i in range(0, 10005)]
        i = 10003
        self.fso.jump(10004)
        while i > 0:
            self.assertEqual(mylist[i], self.fso.previous())
            i -= 1

    def testprevjump(self):
        """check current"""
        self.fso.jump(9999)
        self.assertEqual("mydata9999.edf", self.fso.current())
        self.assertEqual("mydata9998.edf", self.fso.previous())

    def testnextjump(self):
        """check current"""
        self.fso.jump(9999)
        self.assertEqual("mydata9999.edf", self.fso.current())
        self.assertEqual("mydata10000.edf", self.fso.next())

    def testlen(self):
        """check len"""
        self.assertEqual(self.fso.len(), 10006)  # +1 for 0000


class TestFileSeries(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp_directory = os.path.join(UtilsTest.tempdir, cls.__name__)
        os.makedirs(cls.tmp_directory)
        cls.create_resources()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp_directory)

    @classmethod
    def create_resources(cls):
        data = (numpy.random.rand(8, 8) * 10).astype(int)
        data0 = numpy.zeros((8, 8), dtype=int)
        data1 = numpy.zeros((8, 8), dtype=int) + 1
        data2 = numpy.zeros((8, 8), dtype=int) + 2

        # Single frame
        cls.create_edf_file("image_a_000.edf", [data0])
        cls.create_edf_file("image_a_001.edf", [data1])
        cls.create_edf_file("image_a_002.edf", [data2])

        # Many frames
        cls.create_edf_file("image_b_000.edf", [data0, data, data])
        cls.create_edf_file("image_b_001.edf", [data, data, data1])
        cls.create_edf_file("image_b_002.edf", [data2])

        # Any frames
        cls.create_edf_file("image_c_000.edf", [data0, data, data])
        cls.create_edf_file("image_c_001.edf", [data, data1])
        cls.create_edf_file("image_c_002.edf", [data, data, data, data])
        cls.create_edf_file("image_c_003.edf", [data2])

    @classmethod
    def get_filename(cls, filename):
        return os.path.join(cls.tmp_directory, filename)

    @classmethod
    def create_edf_file(cls, filename, data_list):
        filename = cls.get_filename(filename)
        image = fabio.factory("edfimage")
        for frame_id, data in enumerate(data_list):
            header = {"frame_id": "%d" % frame_id, "filename": "%s" % filename}
            if frame_id == 0:
                image.data = data
                image.header.update(header)
            else:
                image.append_frame(data=data, header=header)
        image.write(filename)

    def get_singleframe_files(self):
        filenames = ["image_a_000.edf", "image_a_001.edf", "image_a_002.edf"]
        filenames = [self.get_filename(f) for f in filenames]
        return filenames

    def get_multiframe_files(self):
        filenames = ["image_b_000.edf", "image_b_001.edf", "image_b_002.edf"]
        filenames = [self.get_filename(f) for f in filenames]
        return filenames

    def get_anyframe_files(self):
        filenames = ["image_c_000.edf", "image_c_001.edf", "image_c_002.edf", "image_c_003.edf"]
        filenames = [self.get_filename(f) for f in filenames]
        return filenames

    def test_singleframe_nofiles(self):
        serie = FileSeries(filenames=[], single_frame=True)
        self.assertEqual(serie.nframes, 0)
        for _ in serie.frames():
            self.fail()
        self.assertRaises(IndexError, serie.get_frame, 0)
        serie.close()

    def test_singleframe_nframes(self):
        filenames = self.get_singleframe_files()
        serie = FileSeries(filenames=filenames, single_frame=True)
        self.assertTrue(serie.nframes, 3)
        serie.close()

    def test_singleframe_nframes2(self):
        filenames = self.get_singleframe_files()
        serie = FileSeries(filenames=filenames, fixed_frames=True)
        self.assertTrue(serie.nframes, 3)
        serie.close()

    def test_singleframe_nframes3(self):
        filenames = self.get_singleframe_files()
        serie = FileSeries(filenames=filenames, fixed_frame_number=1)
        self.assertTrue(serie.nframes, 3)
        serie.close()

    def test_singleframe_getframe(self):
        filenames = self.get_singleframe_files()
        serie = FileSeries(filenames=filenames, single_frame=True)
        self.assertRaises(IndexError, serie.get_frame, -1)
        self.assertEqual(serie.get_frame(0).data[0, 0], 0)
        self.assertEqual(serie.get_frame(1).data[0, 0], 1)
        self.assertEqual(serie.get_frame(2).data[0, 0], 2)
        self.assertRaises(IndexError, serie.get_frame, 4)
        serie.close()

    def test_singleframe_frames(self):
        filenames = self.get_singleframe_files()
        serie = FileSeries(filenames=filenames, single_frame=True)
        for frame_id, frame in enumerate(serie.frames()):
            self.assertEqual(frame.data[0, 0], frame_id)
            self.assertEqual(frame.header["frame_id"], "0")
            self.assertIn("%03d" % frame_id, frame.header["filename"])
        self.assertEqual(frame_id, 2)
        serie.close()

    def test_multiframe_nofiles(self):
        serie = FileSeries(filenames=[], fixed_frames=True)
        self.assertEqual(serie.nframes, 0)
        for _ in serie.frames():
            self.fail()
        self.assertRaises(IndexError, serie.get_frame, 0)
        serie.close()

    def test_multiframe_nframes(self):
        filenames = self.get_multiframe_files()
        serie = FileSeries(filenames=filenames, fixed_frames=True)
        self.assertTrue(serie.nframes, 7)
        serie.close()

    def test_multiframe_getframe(self):
        filenames = self.get_multiframe_files()
        serie = FileSeries(filenames=filenames, fixed_frames=True)
        self.assertRaises(IndexError, serie.get_frame, -1)
        self.assertEqual(serie.get_frame(0).data[0, 0], 0)
        self.assertEqual(serie.get_frame(5).data[0, 0], 1)
        self.assertEqual(serie.get_frame(6).data[0, 0], 2)
        self.assertRaises(IndexError, serie.get_frame, 7)
        serie.close()

    def test_multiframe_frames(self):
        filenames = self.get_multiframe_files()
        serie = FileSeries(filenames=filenames, fixed_frames=True)
        for frame_id, frame in enumerate(serie.frames()):
            if frame_id not in [0, 5, 6]:
                continue
            expected_frame_id = {0: 0, 5: 2, 6: 0}[frame_id]
            expected_file_num = {0: 0, 5: 1, 6: 2}[frame_id]
            expected_data = {0: 0, 5: 1, 6: 2}[frame_id]

            self.assertEqual(frame.data[0, 0], expected_data)
            self.assertEqual(frame.header["frame_id"], "%d" % expected_frame_id)
            self.assertIn("%03d" % expected_file_num, frame.header["filename"])
        self.assertEqual(frame_id, 6)
        serie.close()

    def test_anyframe_nofiles(self):
        serie = FileSeries(filenames=[], fixed_frames=False)
        self.assertEqual(serie.nframes, 0)
        for _ in serie.frames():
            self.fail()
        self.assertRaises(IndexError, serie.get_frame, 0)
        serie.close()

    def test_anyframe_nframes(self):
        filenames = self.get_anyframe_files()
        serie = FileSeries(filenames=filenames, fixed_frames=False)
        self.assertTrue(serie.nframes, 10)
        serie.close()

    def test_anyframe_getframe(self):
        filenames = self.get_anyframe_files()
        serie = FileSeries(filenames=filenames, fixed_frames=False)
        self.assertRaises(IndexError, serie.get_frame, -1)
        self.assertEqual(serie.get_frame(0).data[0, 0], 0)
        # Reach frame 3 to force frame 4 to come from the file description cache
        serie.get_frame(3)
        self.assertEqual(serie.get_frame(4).data[0, 0], 1)
        self.assertEqual(serie.get_frame(9).data[0, 0], 2)
        self.assertRaises(IndexError, serie.get_frame, 10)
        serie.close()

    def test_anyframe_getframes(self):
        filenames = self.get_anyframe_files()
        serie = FileSeries(filenames=filenames, fixed_frames=False)
        for frame_id in range(serie.nframes):
            frame = serie.get_frame(frame_id)
            if frame_id not in [0, 4, 9]:
                continue
            expected_file_frame_id = {0: 0, 4: 1, 9: 0}[frame_id]
            expected_file_num = {0: 0, 4: 1, 9: 3}[frame_id]
            expected_data = {0: 0, 4: 1, 9: 2}[frame_id]
            expected_filename = filenames[expected_file_num]

            self.assertEqual(frame.data[0, 0], expected_data)
            self.assertEqual(frame.header["frame_id"], "%d" % expected_file_frame_id)
            self.assertEqual(frame.index, frame_id)
            self.assertEqual(frame.file_index, expected_file_frame_id)
            self.assertIs(frame.container, serie)
            self.assertIs(frame.file_container.filename, expected_filename)
            self.assertIn("%03d" % expected_file_num, frame.header["filename"])
        self.assertEqual(frame_id, 9)
        serie.close()

    def test_anyframe_frames(self):
        filenames = self.get_anyframe_files()
        serie = FileSeries(filenames=filenames, fixed_frames=False)
        for frame_id, frame in enumerate(serie.frames()):
            if frame_id not in [0, 4, 9]:
                continue
            expected_file_frame_id = {0: 0, 4: 1, 9: 0}[frame_id]
            expected_file_num = {0: 0, 4: 1, 9: 3}[frame_id]
            expected_data = {0: 0, 4: 1, 9: 2}[frame_id]
            expected_filename = filenames[expected_file_num]

            self.assertEqual(frame.data[0, 0], expected_data)
            self.assertEqual(frame.header["frame_id"], "%d" % expected_file_frame_id)
            self.assertEqual(frame.index, frame_id)
            self.assertEqual(frame.file_index, expected_file_frame_id)
            self.assertIs(frame.container, serie)
            self.assertIs(frame.file_container.filename, expected_filename)
            self.assertIn("%03d" % expected_file_num, frame.header["filename"])
        self.assertEqual(frame_id, 9)
        serie.close()

    def test_filename_iterator(self):
        filenames = self.get_anyframe_files()
        serie = FileSeries(filenames=iter(filenames))
        self.assertEqual(serie.nframes, 10)
        serie.close()

    def test_filename_generator(self):

        def generator():
            filenames = self.get_anyframe_files()
            for filename in filenames:
                yield filename

        serie = FileSeries(filenames=generator())
        self.assertEqual(serie.nframes, 10)
        serie.close()

    def test_with_numbered_file_series(self):
        filenames = numbered_file_series(self.get_filename("image_c_"), 0, 3, ".edf", digits=3)
        serie = FileSeries(filenames=filenames)
        self.assertEqual(serie.nframes, 10)
        serie.close()

    def test_with_filename_series(self):
        first_filename = self.get_filename("image_c_000.edf")
        filenames = filename_series(first_filename)
        serie = FileSeries(filenames=filenames)
        self.assertEqual(serie.nframes, 10)
        serie.close()


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestRandomSeries))
    testsuite.addTest(loadTests(TestEdfNumbered))
    testsuite.addTest(loadTests(TestFileSeries))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
