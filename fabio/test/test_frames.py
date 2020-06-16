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
Test frame concept of FabioImage

"""

import unittest
import logging
import numpy
import contextlib

logger = logging.getLogger(__name__)

import fabio.fabioimage
import fabio.edfimage
import fabio.file_series
from .utilstest import UtilsTest


class _CommonTestFrames(unittest.TestCase):
    """Test generic tests which could append on frame iteration"""

    @classmethod
    def getMeta(cls):
        return None

    @classmethod
    def setUpClass(cls):
        cls.meta = cls.getMeta()
        if cls.meta is None:
            raise unittest.SkipTest("No data test")

    @contextlib.contextmanager
    def image(self):
        if hasattr(self.meta, "image"):
            image = self.meta.image
            if image is not None:
                yield image
                return

        image = fabio.open(self.meta.filename)
        try:
            yield image
        finally:
            image.close()

    def test_frames_full_iteration(self):
        with self.image() as image:
            cache = {}
            for i, frame in enumerate(image.frames()):
                cache["data %d" % i] = numpy.array(frame.data)
                cache["header %d" % i] = frame.header.copy()
                self.assertEqual(i, frame.index)
            self.assertEqual(i, self.meta.nframes - 1)
            for i, frame in enumerate(image.frames()):
                data = cache.pop("data %d" % i)
                self.assertTrue(numpy.array_equal(data, frame.data))
                header = cache.pop("header %d" % i)
                self.assertEqual(header, frame.header)
                self.assertEqual(i, frame.index)
            self.assertEqual(len(cache), 0)
            self.assertEqual(i, self.meta.nframes - 1)
            self.assertEqual(image.nframes, self.meta.nframes)

    def test_frames_abort_iteration(self):
        with self.image() as image:
            for i, _frame in enumerate(image.frames()):
                if i == 2:
                    break
            for i, _frame in enumerate(image.frames()):
                pass
            self.assertEqual(i, self.meta.nframes - 1)
            self.assertEqual(image.nframes, self.meta.nframes)

    def test_frames_random_access(self):
        with self.image() as image:
            nframes = self.meta.nframes
            self.assertEqual(image.nframes, nframes)

            # before last
            frame2 = image._get_frame(nframes - 2)
            # first
            frame1 = image._get_frame(0)
            # last
            frame3 = image._get_frame(nframes - 1)

            self.assertIsNotNone(frame1)
            self.assertIsNotNone(frame2)
            self.assertIsNotNone(frame3)
            self.assertEqual(frame1.index, 0)
            self.assertEqual(frame2.index, nframes - 2)
            self.assertEqual(frame3.index, nframes - 1)
            self.assertIsNot(frame1, frame2)
            self.assertIsNot(frame2, frame3)
            self.assertIsNot(frame3, frame1)
            self.assertEqual(image.nframes, self.meta.nframes)


class TestVirtualEdf(_CommonTestFrames):

    @classmethod
    def getMeta(cls):
        header1 = {"foo": "bar"}
        data1 = numpy.array([[1, 1], [3, 4]], dtype=numpy.uint16)
        header2 = {"foo": "bar2"}
        data2 = numpy.array([[2, 2], [3, 4]], dtype=numpy.uint16)
        header3 = {"foo": "bar2"}
        data3 = numpy.array([[3, 3], [3, 4]], dtype=numpy.uint16)
        image = fabio.edfimage.EdfImage(data=data1, header=header1)
        image.append_frame(data=data2, header=header2)
        image.append_frame(data=data3, header=header3)
        frames = [(header1, data1), (header2, data2), (header3, data3)]

        class Meta(object):
            pass

        meta = Meta()
        meta.image = image
        meta.nframes = 3
        meta.frames = frames
        return meta

    def test_content(self):
        image = self.meta.image
        frames = self.meta.frames
        for i, frame in enumerate(image.frames()):
            header, data = frames[i]
            if i in [0, 1, 2]:
                self.assertIsInstance(frame, fabio.fabioimage.FabioFrame)
                self.assertIs(frame.file_container, image)
                self.assertEqual(frame.header["foo"], header["foo"])
                self.assertEqual(frame.file_index, i)
                self.assertEqual(frame.shape, data.shape)
                self.assertEqual(frame.dtype, data.dtype)
                self.assertEqual(frame.data[0, 0], i + 1)
                self.assertTrue(numpy.array_equal(frame.data, data))
            else:
                self.fail()


class TestEdf(_CommonTestFrames):

    @classmethod
    def getMeta(cls):
        filename = UtilsTest.getimage("multiframes.edf.bz2")
        filename = filename.replace(".bz2", "")
        image = fabio.open(filename)

        class Meta(object):
            pass

        meta = Meta()
        meta.image = image
        meta.nframes = 8
        return meta

    def test_content(self):
        image = self.meta.image
        self.assertEqual(image.nframes, 8)
        for i, frame in enumerate(image.frames()):
            if 0 <= i < 8:
                self.assertIsInstance(frame, fabio.fabioimage.FabioFrame)
                self.assertIs(frame.file_container, image)
                self.assertEqual(frame.file_index, i)
                self.assertEqual(frame.data[0, 0], i)
                self.assertEqual(frame.shape, (40, 20))
                self.assertEqual(frame.dtype, numpy.dtype("uint16"))
            else:
                self.fail()


class TestTiff(_CommonTestFrames):

    @classmethod
    def getMeta(cls):
        filename = UtilsTest.getimage("multiframes.tif.bz2")
        filename = filename.replace(".bz2", "")
        image = fabio.open(filename)

        class Meta(object):
            pass

        meta = Meta()
        meta.image = image
        meta.nframes = 8
        return meta

    def test_content(self):
        image = self.meta.image
        self.assertEqual(image.nframes, 8)
        for i, frame in enumerate(image.frames()):
            if 0 <= i < 8:
                self.assertIsInstance(frame, fabio.fabioimage.FabioFrame)
                self.assertIs(frame.file_container, image)
                self.assertEqual(frame.file_index, i)
                self.assertEqual(frame.data[0, 0], i)
                self.assertEqual(frame.shape, (40, 20))
                self.assertEqual(frame.dtype, numpy.dtype("uint16"))
            else:
                self.fail()


class TestFabioImage(unittest.TestCase):

    def test_single_frame_iterator(self):
        data = numpy.array([[1, 2], [3, 4]], dtype=numpy.uint16)
        image = fabio.fabioimage.FabioImage(data=data)
        for i, frame in enumerate(image.frames()):
            if i == 0:
                self.assertIsInstance(frame, fabio.fabioimage.FabioFrame)
                self.assertIs(frame.file_container, image)
                self.assertEqual(frame.file_index, 0)
                self.assertEqual(frame.shape, data.shape)
                self.assertEqual(frame.dtype, data.dtype)
                self.assertTrue(numpy.array_equal(frame.data, data))
            else:
                self.fail()


class TestFileSeries(_CommonTestFrames):

    @classmethod
    def getMeta(cls):
        filenames = []
        filename = UtilsTest.getimage("multiframes.tif.bz2")
        filename = filename.replace(".bz2", "")
        filenames.append(filename)
        filename = UtilsTest.getimage("multiframes.edf.bz2")
        filename = filename.replace(".bz2", "")
        filenames.append(filename)
        image = fabio.file_series.FileSeries(filenames)

        class Meta(object):
            pass

        meta = Meta()
        meta.image = image
        meta.nframes = 8 * 2
        return meta


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestFabioImage))
    testsuite.addTest(loadTests(TestVirtualEdf))
    testsuite.addTest(loadTests(TestEdf))
    testsuite.addTest(loadTests(TestTiff))
    testsuite.addTest(loadTests(TestFileSeries))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
