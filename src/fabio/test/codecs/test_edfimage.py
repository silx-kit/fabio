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
# Unit tests

# builds on stuff from ImageD11.test.testpeaksearch
28/11/2014
"""

import unittest
import os
import numpy
import shutil
import io
import logging

logger = logging.getLogger(__name__)

import fabio
from ...edfimage import edfimage
from ...fabioutils import GzipFile, BZ2File
from ..utilstest import UtilsTest
from ..testutils import LoggingValidator 


class TestFlatEdfs(unittest.TestCase):
    """ test some flat images """

    def common_setup(self):
        self.BYTE_ORDER = "LowByteFirst" if numpy.little_endian else "HighByteFirst"
        self.MYHEADER = ("{\n%-1020s}\n" % (
                        """Omega = 0.0 ;
                        Dim_1 = 256 ;
                        Dim_2 = 256 ;
                        DataType = FloatValue ;
                        ByteOrder = %s ;
                        Image = 1;
                        History-1 = something=something else;
                        \n\n""" % self.BYTE_ORDER)).encode("latin-1")
        self.MYIMAGE = numpy.ones((256, 256), numpy.float32) * 10
        self.MYIMAGE[0, 0] = 0
        self.MYIMAGE[1, 1] = 20

        assert len(self.MYIMAGE[0:1, 0:1].tobytes()) == 4, self.MYIMAGE[0:1, 0:1].tobytes()

    def setUp(self):
        """ initialize"""
        self.common_setup()
        self.filename = os.path.join(UtilsTest.tempdir, "im0000.edf")
        if not os.path.isfile(self.filename):
            outf = open(self.filename, "wb")
            assert len(self.MYHEADER) % 1024 == 0
            outf.write(self.MYHEADER)
            outf.write(self.MYIMAGE.tobytes())
            outf.close()

        obj = edfimage()
        obj.read(self.filename)
        self.obj = obj

    def tearDown(self):
        self.obj.close()
        self.obj = None
        unittest.TestCase.tearDown(self)
        self.BYTE_ORDER = self.MYHEADER = self.MYIMAGE = None

    def test_read(self):
        """ check readable"""
        self.assertEqual(self.obj.shape, (256, 256), msg="File %s has wrong shape " % self.filename)
        self.assertEqual(self.obj.bpp, 4, msg="bpp!=4 for file: %s" % self.filename)
        self.assertEqual(self.obj.bytecode, numpy.float32, msg="bytecode!=flot32 for file: %s" % self.filename)
        self.assertEqual(self.obj.data.shape, (256, 256), msg="shape!=(256,256) for file: %s" % self.filename)

    def test_getstats(self):
        """ test statistics"""
        self.assertEqual(self.obj.getmean(), 10)
        self.assertEqual(self.obj.getmin(), 0)
        self.assertEqual(self.obj.getmax(), 20)

    def test_headers(self):
        self.assertEqual(len(self.obj.header), 7)
        expected_keys = ["Omega", "Dim_1", "Dim_2", "DataType", "ByteOrder", "Image", "History-1"]
        self.assertEqual(expected_keys, list(self.obj.header.keys()))

        expected_values = {
            "Omega": "0.0",
            "Dim_1": "256",
            "Dim_2": "256",
            "DataType": "FloatValue",
            "Image": "1",
            "History-1": "something=something else"
        }
        for k, expected_value in expected_values.items():
            self.assertEqual(self.obj.header[k], expected_value)


class TestBzipEdf(TestFlatEdfs):
    """ same for bzipped versions """

    def setUp(self):
        """set it up"""
        TestFlatEdfs.setUp(self)
        if not os.path.isfile(self.filename + ".bz2"):
            with BZ2File(self.filename + ".bz2", "wb") as f:
                with open(self.filename, "rb") as d:
                    f.write(d.read())
        self.filename += ".bz2"


class TestGzipEdf(TestFlatEdfs):
    """ same for gzipped versions """

    def setUp(self):
        """ set it up """
        TestFlatEdfs.setUp(self)
        if not os.path.isfile(self.filename + ".gz"):
            with GzipFile(self.filename + ".gz", "wb") as f:
                with open(self.filename, "rb") as d:
                    f.write(d.read())
        self.filename += ".gz"


# statistics come from fit2d I think
# filename dim1 dim2 min max mean stddev
TESTIMAGES = """F2K_Seb_Lyso0675.edf     2048 2048 982 17467 1504.29  217.61
                F2K_Seb_Lyso0675.edf.bz2 2048 2048 982 17467 1504.29  217.61
                F2K_Seb_Lyso0675.edf.gz  2048 2048 982 17467 1504.29  217.61
                id13_badPadding.edf      512  512  85  61947 275.62   583.44 """


class TestEdfs(unittest.TestCase):
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
            shape = dim2, dim1
            mini, maxi, mean, stddev = [float(x) for x in vals[3:]]
            obj = edfimage()
            try:
                obj.read(os.path.join(self.im_dir, name))
            except Exception:
                logger.error("Cannot read image %s", name)
                raise
            self.assertAlmostEqual(mini, obj.getmin(), 2, "testedfs: %s getmin()" % name)
            self.assertAlmostEqual(maxi, obj.getmax(), 2, "testedfs: %s getmax" % name)
            logger.info("%s Mean: exp=%s, obt=%s" % (name, mean, obj.getmean()))
            self.assertAlmostEqual(mean, obj.getmean(), 2, "testedfs: %s getmean" % name)
            logger.info("%s StdDev:  exp=%s, obt=%s" % (name, stddev, obj.getstddev()))
            self.assertAlmostEqual(stddev, obj.getstddev(), 2, "testedfs: %s getstddev" % name)
            self.assertEqual(obj.shape, shape, "testedfs: %s shape" % name)
        obj = None

    def test_rebin(self):
        """test the rebin of edfdata"""
        f = edfimage()
        f.read(os.path.join(self.im_dir, "F2K_Seb_Lyso0675.edf"))
        f.rebin(1024, 1024)
        self.assertEqual(abs(numpy.array([[1547, 1439], [1536, 1494]]) - f.data).max(), 0, "data are the same after rebin")

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        self.im_dir = None


class TestEdfCompressedData(unittest.TestCase):
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

        ref.read(os.path.join(self.im_dir, refFile))
        gzipped.read(os.path.join(self.im_dir, gzippedFile))
        compressed.read(os.path.join(self.im_dir, compressedFile))

        self.assertEqual((ref.data - gzipped.data).max(), 0, "Gzipped data block is correct")
        self.assertEqual((ref.data - compressed.data).max(), 0, "Zlib compressed data block is correct")


class TestEdfMultiFrame(unittest.TestCase):
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

        self.ref.read(self.multiFrameFilename)
        self.frame0.read(self.Frame0Filename)
        self.frame1.read(self.Frame1Filename)

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        self.multiFrameFilename = self.Frame0Filename = self.Frame1Filename = self.ref = self.frame0 = self.frame1 = None

    def test_getFrame_multi(self):
        self.assertEqual((self.ref.data - self.frame0.data).max(), 0, "getFrame_multi: Same data for frame 0")
        f1_multi = self.ref.getframe(1)
        # logger.warning("f1_multi.header=%s\nf1_multi.data=  %s" % (f1_multi.header, f1_multi.data))
        self.assertEqual((f1_multi.data - self.frame1.data).max(), 0, "getFrame_multi: Same data for frame 1")

    def test_getFrame_mono(self):
        self.assertEqual((self.ref.data - self.frame0.data).max(), 0, "getFrame_mono: Same data for frame 0")
        f1_mono = self.frame0.getframe(1)
        self.assertEqual((f1_mono.data - self.frame1.data).max(), 0, "getFrame_mono: Same data for frame 1")

    def test_next_multi(self):
        self.assertEqual((self.ref.data - self.frame0.data).max(), 0, "next_multi: Same data for frame 0")
        next_ = self.ref.next()
        self.assertEqual((next_.data - self.frame1.data).max(), 0, "next_multi: Same data for frame 1")

    def text_next_mono(self):
        self.assertEqual((self.ref.data - self.frame0.data).max(), 0, "next_mono: Same data for frame 0")
        next_ = self.frame0.next()
        self.assertEqual((next_.data - self.frame1.data).max(), 0, "next_mono: Same data for frame 1")

    def test_previous_multi(self):
        f1 = self.ref.getframe(1)
        self.assertEqual((f1.data - self.frame1.data).max(), 0, "previous_multi: Same data for frame 1")
        f0 = f1.previous()
        self.assertEqual((f0.data - self.frame1.data).max(), 0, "previous_multi: Same data for frame 0")

    def test_previous_mono(self):
        f1 = self.ref.getframe(1)
        self.assertEqual((f1.data - self.frame1.data).max(), 0, "previous_mono: Same data for frame 1")
        prev = self.frame1.previous()
        self.assertEqual((prev.data - self.frame0.data).max(), 0, "previous_mono: Same data for frame 0")

    def test_openimage_multiframes(self):
        "test if openimage can directly read first or second frame of a multi-frame"
        self.assertEqual((fabio.open(self.multiFrameFilename).data - self.frame0.data).max(), 0, "openimage_multiframes: Same data for default ")
        # print(fabio.open(self.multiFrameFilename, 0).data)
        self.assertEqual((fabio.open(self.multiFrameFilename, 0).data - self.frame0.data).max(), 0, "openimage_multiframes: Same data for frame 0")
        self.assertEqual((fabio.open(self.multiFrameFilename, 1).data - self.frame1.data).max(), 0, "openimage_multiframes: Same data for frame 1")


class TestEdfFastRead(unittest.TestCase):
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
        obt = ref.fast_read_data(self.fastFilename)
        self.assertEqual(abs(obt - refdata).max(), 0, "testedffastread: Same data")


class TestEdfWrite(unittest.TestCase):
    """
    Write dummy edf files with various compression schemes
    """
    tmpdir = UtilsTest.tempdir

    def setUp(self):
        self.data = numpy.arange(100).reshape((10, 10))
        self.header = {"toto": "tutu"}

    def testFlat(self):
        self.filename = os.path.join(self.tmpdir, "merged.azim")
        e = edfimage(data=self.data, header=self.header)
        e.write(self.filename)
        r = fabio.open(self.filename)
        self.assertTrue(r.header["toto"] == self.header["toto"], "header are OK")
        self.assertTrue(abs(r.data - self.data).max() == 0, "data are OK")
        self.assertEqual(int(r.header["EDF_HeaderSize"]), 512, "header size is one 512 block")

    def testGzip(self):
        self.filename = os.path.join(self.tmpdir, "merged.azim.gz")
        e = edfimage(data=self.data, header=self.header)
        e.write(self.filename)
        r = fabio.open(self.filename)
        self.assertTrue(r.header["toto"] == self.header["toto"], "header are OK")
        self.assertTrue(abs(r.data - self.data).max() == 0, "data are OK")
        self.assertEqual(int(r.header["EDF_HeaderSize"]), 512, "header size is one 512 block")

    def testBzip2(self):
        self.filename = os.path.join(self.tmpdir, "merged.azim.gz")
        e = edfimage(data=self.data, header=self.header)
        e.write(self.filename)
        r = fabio.open(self.filename)
        self.assertTrue(r.header["toto"] == self.header["toto"], "header are OK")
        self.assertTrue(abs(r.data - self.data).max() == 0, "data are OK")
        self.assertEqual(int(r.header["EDF_HeaderSize"]), 512, "header size is one 512 block")

    def tearDown(self):
        os.unlink(self.filename)


class TestEdfRegression(unittest.TestCase):
    """
    Test suite to prevent regression
    """

    def test_bug_27(self):
        """
        import fabio
        obj = fabio.open("any.edf")
        obj.header["missing"]="blah"
        obj.write("any.edf")
        """
        # create dummy image:
        shape = (32, 32)
        data = numpy.random.randint(0, 6500, size=shape[0] * shape[1]).astype("uint16").reshape(shape)
        fname = os.path.join(UtilsTest.tempdir, "bug27.edf")
        e = edfimage(data=data, header={"key1": "value1"})
        e.write(fname)
        del e

        obj = fabio.open(fname)
        obj.header["missing"] = "blah"
        obj.write(fname)

        del obj

    def test_remove_metadata_header(self):
        filename = UtilsTest.getimage("face.edf.bz2")[0:-4]
        output_filename = os.path.join(UtilsTest.tempdir, "test_remove_metadata_header.edf")

        image = fabio.open(filename)
        del image.header["Dim_1"]
        image.write(output_filename)
        image2 = fabio.open(output_filename)
        self.assertEqual(image.shape, image2.shape)

    def test_bug_459(self):
        h = {'HeaderID': 'EH:000001:000000:000000',
             'Image': '1',
             'ByteOrder': 'LowByteFirst',
             'DataType': 'Float',
             'Dim_1': '3216',
             'Dim_2': '3000',
             'Size': '38592000',
             'Date': '30-Oct-2021',
             'Lcurve': '0',
             'Mh': '24.996',
             'Mv': '24.996',
             'angles_fname': 'angles_file.txt',
             'angles_sign': '-1',
             'ans': ';',
             'approach': '8',
             'argn': '[0,',
             'avg_plane_zero': '6.2031',
             'axisfilesduringscan': '1',
             'axisposition': 'global',
             'betash': '0.0179803',
             'betasv': '0.0179803',
             'calc_residu': '0',
             'centralpart': '2048',
             'centralpart_shift_h': '0',
             'centralpart_shift_v': '0',
             'centralpart_struct': ';',
             'check_spectrum': '0',
             'check_z1v': '0',
             'constrain': '0',
             'correct_detector': '3',
             'correct_distortion_par': ';',
             'correct_shrink': '0',
             'correct_shrink_positive': '0',
             'correct_whitefield_par': '17',
             'cutn': '0.0511098',
             'cylinder': '0',
             'debug': '0',
             'delta_beta': '2119.4',
             'delta_beta_normalised': '0',
             'delta_beta_range': '2119.4',
             'delta_beta_test': '0',
             'dim_h': '2048',
             'dim_v': '2048',
             'dir': '/data/visitor/ls3023/id16a/PR3/',
             'direc': ''}
        with LoggingValidator(fabio.edfimage.logger, error=0, warning=0):
            fabio.edfimage.EdfFrame.get_data_rank(h)
        
    
class TestBadFiles(unittest.TestCase):

    filename_template = "%s.edf"

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
        filename = os.path.join(cls.tmp_directory, cls.filename_template % "base")
        cls.base_filename = filename
        with io.open(filename, "wb") as fd:
            cls.write_header(fd, 1)
            cls.header1 = fd.tell()
            cls.write_data(fd)
            cls.data1 = fd.tell()
            cls.write_header(fd, 2)
            cls.header2 = fd.tell()
            cls.write_data(fd)
            cls.data2 = fd.tell()

    @classmethod
    def write_header(cls, fd, image_number):
        byte_order = "LowByteFirst" if numpy.little_endian else "HighByteFirst"
        byte_order = byte_order.encode("latin-1")

        fd.write(b"{\n")
        fd.write(b"Omega = 0.0 ;\n")
        fd.write(b"Dim_1 = 256 ;\n")
        fd.write(b"Dim_2 = 256 ;\n")
        fd.write(b"DataType = FloatValue ;\n")
        fd.write(b"ByteOrder = %s ;\n" % byte_order)
        fd.write(b"Image = %d ;\n" % image_number)
        fd.write(b"History-1 = something=something else;\n")
        fd.write(b"}\n")

    @classmethod
    def write_data(cls, fd):
        data = numpy.ones((256, 256), numpy.float32) * 10
        data[0, 0] = 0
        data[1, 1] = 20
        fd.write(data.tobytes())

    @classmethod
    def copy_base(cls, filename, size):
        with io.open(cls.base_filename, "rb") as fd_base:
            with io.open(filename, "wb") as fd_result:
                fd_result.write(fd_base.read(size))

    @classmethod
    def open(cls, filename):
        image = fabio.edfimage.EdfImage()
        image.read(filename)
        return image

    def test_base(self):
        filename = os.path.join(self.tmp_directory, self.filename_template % str(self.id()))
        size = self.data2
        self.copy_base(filename, size)

        image = self.open(filename)
        self.assertEqual(image.nframes, 2)

        frame = image.getframe(0)
        self.assertEqual(frame.header["Image"], "1")
        self.assertEqual(frame.data[-1].sum(), 2560)
        frame = image.getframe(1)
        self.assertEqual(frame.header["Image"], "2")
        self.assertEqual(frame.data[-1].sum(), 2560)

    def test_empty(self):
        filename = os.path.join(self.tmp_directory, self.filename_template % str(self.id()))
        f = io.open(filename, "wb")
        f.close()

        self.assertRaises(IOError, self.open, filename)

    def test_wrong_magic(self):
        filename = os.path.join(self.tmp_directory, self.filename_template % str(self.id()))
        f = io.open(filename, "wb")
        f.write(b"\x10\x20\x30")
        f.close()

        self.assertRaises(IOError, self.open, filename)

    def test_half_header(self):
        filename = os.path.join(self.tmp_directory, self.filename_template % str(self.id()))
        size = self.header1 // 2
        self.copy_base(filename, size)

        self.assertRaises(IOError, self.open, filename)

    def test_header_with_no_data(self):
        filename = os.path.join(self.tmp_directory, self.filename_template % str(self.id()))
        size = self.header1
        self.copy_base(filename, size)

        image = self.open(filename)
        self.assertIn(image.nframes, [0, 1])
        self.assertTrue(image.incomplete_file)

    def test_header_with_half_data(self):
        filename = os.path.join(self.tmp_directory, self.filename_template % str(self.id()))
        size = (self.header1 + self.data1) // 2
        self.copy_base(filename, size)

        image = self.open(filename)
        self.assertEqual(image.nframes, 1)
        self.assertTrue(image.incomplete_file)

        frame = image
        self.assertEqual(frame.header["Image"], "1")
        self.assertEqual(frame.data[-1].sum(), 0)
        self.assertTrue(frame.incomplete_data)

    def test_full_frame_plus_half_header(self):
        filename = os.path.join(self.tmp_directory, self.filename_template % str(self.id()))
        size = (self.data1 + self.header2) // 2
        self.copy_base(filename, size)

        image = self.open(filename)
        self.assertEqual(image.nframes, 1)
        self.assertTrue(image.incomplete_file)

        frame = image
        self.assertEqual(frame.header["Image"], "1")
        self.assertEqual(frame.data[-1].sum(), 2560)
        self.assertFalse(frame.incomplete_data)

    def test_full_frame_plus_header_with_no_data(self):
        filename = os.path.join(self.tmp_directory, self.filename_template % str(self.id()))
        size = self.header2
        self.copy_base(filename, size)

        image = self.open(filename)
        self.assertIn(image.nframes, [1, 2])
        self.assertTrue(image.incomplete_file)

        frame = image
        self.assertEqual(frame.header["Image"], "1")
        self.assertEqual(frame.data[-1].sum(), 2560)
        self.assertFalse(frame.incomplete_data)

    def test_full_frame_plus_header_with_half_data(self):
        filename = os.path.join(self.tmp_directory, self.filename_template % str(self.id()))
        size = (self.header2 + self.data2) // 2
        self.copy_base(filename, size)

        image = self.open(filename)
        self.assertEqual(image.nframes, 2)
        self.assertTrue(image.incomplete_file)

        frame = image.getframe(0)
        self.assertEqual(frame.header["Image"], "1")
        self.assertEqual(frame.data[-1].sum(), 2560)
        self.assertFalse(frame.incomplete_data)

        frame = image.getframe(1)
        self.assertEqual(frame.header["Image"], "2")
        self.assertEqual(frame.data[-1].sum(), 0)
        self.assertTrue(frame.incomplete_data)


class TestBadGzFiles(TestBadFiles):

    filename_template = "%s.edf.gz"

    @classmethod
    def write_header(cls, fd, image_number):
        with GzipFile(fileobj=fd, mode="wb") as gzfd:
            TestBadFiles.write_header(gzfd, image_number)

    @classmethod
    def write_data(cls, fd):
        with GzipFile(fileobj=fd, mode="wb") as gzfd:
            TestBadFiles.write_data(gzfd)


class TestSphere2SaxsSamples(unittest.TestCase):
    """Test some samples from sphere2saxs"""

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.samples = UtilsTest.resources.getdir("sphere2saxs_output.tar.bz2")

    SAMPLES = {
        "multi.edf": (5, (200, 100), numpy.float32, (6.292408e-05, 0.5594252, 3.2911296, 0.82902604)),
        "multi.edf.gz": (5, (200, 100), numpy.float32, (6.292408e-05, 0.5594252, 3.2911296, 0.82902604)),
        "sphere.edf": (1, (200, 100), numpy.float32, (6.292408e-05, 0.5594252, 3.2911296, 0.82902604)),
        "sphere.edf.gz": (1, (200, 100), numpy.float32, (6.292408e-05, 0.5594252, 3.2911296, 0.82902604)),
    }

    def test_all_images(self):
        for filename in self.samples:
            if not os.path.isfile(filename):
                continue
            with fabio.open(filename) as f:
                logger.debug("Reading file %s", filename)
                expected_data = self.SAMPLES[os.path.basename(filename)]
                nframes, shape, dtype, datainfo = expected_data
                self.assertEqual(f.nframes, nframes)
                self.assertEqual(f.shape, shape)
                self.assertEqual(f.dtype, dtype)
                vmin, vmean, vmax, vstd = datainfo
                self.assertEqual(f.dtype, dtype)
                self.assertAlmostEqual(f.data.min(), vmin, places=4)
                self.assertAlmostEqual(f.data.mean(), vmean, places=4)
                self.assertAlmostEqual(f.data.max(), vmax, places=4)
                self.assertAlmostEqual(f.data.std(), vstd, places=4)


class TestEdfIterator(unittest.TestCase):
    """Read different EDF files with lazy iterator
    """

    def test_multi_frame(self):
        """Test iterator on a multi-frame EDF"""
        filename = UtilsTest.getimage("MultiFrame.edf.bz2")

        iterator = fabio.edfimage.EdfImage.lazy_iterator(filename)
        ref = fabio.open(filename)

        for index in range(ref.nframes):
            frame = next(iterator)
            ref_frame = ref.getframe(index)
            self.assertEqual(numpy.abs(ref_frame.data - frame.data).max(), 0, 'Test frame %d data' % index)
            self.assertEqual(ref_frame.header, frame.header, 'Test frame %d header' % index)

        with self.assertRaises(StopIteration):
            next(iterator)

    def test_single_frame(self):
        """Test iterator on a single frame EDF"""
        filename = UtilsTest.getimage("edfCompressed_U16.edf")
        iterator = fabio.edfimage.EdfImage.lazy_iterator(filename)

        frame = next(iterator)
        ref = fabio.open(filename)
        self.assertEqual((ref.data - frame.data).max(), 0, "Test data")
        self.assertEqual(ref.header, frame.header, "Test header")

        with self.assertRaises(StopIteration):
            next(iterator)



class TestEdfBadHeader(unittest.TestCase):
    """Test reader behavior with corrupted header file"""

    def setUp(self):
        self.fgood = os.path.join(UtilsTest.tempdir, "TestEdfGoodHeaderPadding.edf")
        self.fbad = os.path.join(UtilsTest.tempdir, "TestEdfBadHeaderPadding.edf")
        self.fzero = os.path.join(UtilsTest.tempdir, "TestEdfZeroHeaderPadding.edf")
        self.fnonascii = os.path.join(UtilsTest.tempdir, "TestEdfNonAsciiItem.edf")
        self.data = numpy.zeros((10, 11), numpy.uint8)
        self.hdr = {"mykey": "myvalue", "title": "ok"}

        good = fabio.edfimage.edfimage(self.data, self.hdr)
        good.write(self.fgood)
        with fabio.open(self.fgood) as good:
            self.good_header = good.header

        with open(self.fgood, "rb") as fh:
            hdr = bytearray(fh.read(512))
            while hdr.find(b"}") < 0:
                hdr += fh.read(512)
            data = fh.read()
        with open( self.fbad, "wb") as fb:
            start = hdr.rfind(b";") + 1
            end = hdr.find(b"}") - 1
            hdr[start:end] = [ord('\n')] + [0xcd] * (end - start - 1)
            fb.write(hdr)
            fb.write(data)
        with open( self.fzero, "wb") as fb:
            # insert some 0x00 to be stripped
            key = b"myvalue"
            z = hdr.find(key)
            hdr[z + len(key)] = 0
            fb.write(hdr)
            fb.write(data)
        with open( self.fnonascii, "wb") as fb:
            hdr[z:z + 1]= 0xc3, 0xa9  # e-acute in utf-8 ??
            with open(self.fnonascii, "wb") as fb:
                fb.write(hdr)
                fb.write(data)

    def tearDown(self):
        os.remove(self.fgood)
        os.remove(self.fbad)
        os.remove(self.fzero)
        os.remove(self.fnonascii)

    def testReadBadPadding(self):
        """
        Some old data were found with headers padded with 0xcd (issue #373)
        """
        with fabio.open(self.fbad) as im:
            self.assertTrue((im.data == 0).all())
            self.assertEqual(im.header, self.good_header)

    def testReadGoodPadding(self):
        with fabio.open(self.fgood) as im:
            self.assertTrue((im.data == 0).all())
            self.assertEqual(im.header, self.good_header)

    def testReadZeroPadding(self):
        with fabio.open(self.fzero) as im:
            self.assertTrue((im.data == 0).all())
            self.assertEqual(im.header, self.good_header)

    def testNonAsciiHeader(self):
        """Non-ascii characters are skipped."""
        with fabio.open(self.fnonascii) as im:
            self.assertTrue((im.data == 0).all())
            expected = dict(self.good_header)
            expected.pop("mykey")
            self.assertEqual(im.header, expected)

def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestFlatEdfs))
    testsuite.addTest(loadTests(TestBzipEdf))
    testsuite.addTest(loadTests(TestGzipEdf))
    testsuite.addTest(loadTests(TestEdfs))
    testsuite.addTest(loadTests(TestEdfCompressedData))
    testsuite.addTest(loadTests(TestEdfMultiFrame))
    testsuite.addTest(loadTests(TestEdfFastRead))
    testsuite.addTest(loadTests(TestEdfWrite))
    testsuite.addTest(loadTests(TestEdfRegression))
    testsuite.addTest(loadTests(TestBadFiles))
    testsuite.addTest(loadTests(TestBadGzFiles))
    testsuite.addTest(loadTests(TestEdfIterator))
    testsuite.addTest(loadTests(TestSphere2SaxsSamples))
    testsuite.addTest(loadTests(TestEdfBadHeader))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
