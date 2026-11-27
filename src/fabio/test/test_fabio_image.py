#!/usr/bin/env python
#
#    Project: Fable Input Output
#             https://github.com/silx-kit/fabio
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
Test cases for the fabioimage class

testsuite by Jerome Kieffer (Jerome.Kieffer@esrf.eu)
28/11/2014
"""

import copy
import logging
import os
import tempfile
import unittest
from unittest import mock

import numpy

from .. import fabioutils, open as openimage, open_series
from ..cbfimage import CbfImage
from ..edfimage import EdfImage
from ..fabioimage import FabioImage
from ..openimage import _do_magic, openheader
from ..utils import pilutils
from .utilstest import UtilsTest

logger = logging.getLogger(__name__)

try:
    import lzma
except ImportError:
    lzma = None

try:
    import pathlib
except ImportError:
    try:
        import pathlib2 as pathlib
    except ImportError:
        pathlib = None


class Test50000(unittest.TestCase):
    """test with 50000 everywhere"""

    def setUp(self):
        """make the image"""
        dat = numpy.ones((1024, 1024), numpy.uint16)
        dat = (dat * 50000).astype(numpy.uint16)
        assert dat.dtype.char == numpy.ones((1), numpy.uint16).dtype.char
        hed = {"Title": "50000 everywhere"}
        self.obj = FabioImage(dat, hed)

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        self.obj = None

    def testgetmax(self):
        """check max"""
        self.assertEqual(self.obj.getmax(), 50000)

    def testgetmin(self):
        """check min"""
        self.assertEqual(self.obj.getmin(), 50000)

    def testgetmean(self):
        """check mean"""
        self.assertEqual(self.obj.getmean(), 50000)

    def testgetstddev(self):
        """check stddev"""
        self.assertEqual(self.obj.getstddev(), 0)

    def testcopy(self):
        "test the copy statement"
        c = copy.copy(self.obj)
        self.assertNotEqual(id(c), id(self.obj), "object differ")
        self.assertEqual(c.header, self.obj.header, "header are the same")
        self.assertEqual(abs(c.data - self.obj.data).max(), 0, "data are the same")
        self.assertEqual(c.filename, self.obj.filename, "filename is the same")


class TestSlices(unittest.TestCase):
    """check slicing"""

    def setUp(self):
        """make test data"""
        dat2 = numpy.zeros((1024, 1024), numpy.uint16)
        hed = {"Title": "zeros and 100"}
        self.cord = [256, 256, 790, 768]
        self.obj = FabioImage(dat2, hed)
        self.slic = slic = self.obj.make_slice(self.cord)
        # Note - d2 is modified *after* fabioimage is made
        dat2[slic] = dat2[slic] + 100
        assert self.obj.maxval is None
        assert self.obj.minval is None
        self.npix = (slic[0].stop - slic[0].start) * (slic[1].stop - slic[1].start)

    def testgetmax(self):
        """check max"""
        self.assertEqual(self.obj.getmax(), 100)

    def testgetmin(self):
        """check min"""
        self.assertEqual(self.obj.getmin(), 0)

    def testintegratearea(self):
        """check integrations"""
        self.obj.resetvals()
        area1 = self.obj.integrate_area(self.cord)
        self.obj.resetvals()
        area2 = self.obj.integrate_area(self.slic)
        self.assertEqual(area1, area2)
        self.assertEqual(area1, self.npix * 100)

    def testRebin(self):
        """Test the rebin method"""
        big = numpy.arange(64).reshape((8, 8))
        res = numpy.array([[13, 17], [45, 49]])
        fabimg = FabioImage(data=big, header={})
        fabimg.rebin(4, 4)
        self.assertEqual(
            abs(res - fabimg.data).max(), 0, "data are the same after rebin"
        )


class TestOpen(unittest.TestCase):
    """check opening compressed files"""

    testfile = os.path.join(UtilsTest.tempdir, "testfile")

    def setUp(self):
        """create test files"""
        if not os.path.isfile(self.testfile):
            with open(self.testfile, "wb") as f:
                f.write(b"{ hello }")
        if not os.path.isfile(self.testfile + ".gz"):
            with fabioutils.GzipFile(self.testfile + ".gz", "wb") as wf:
                wf.write(b"{ hello }")
        if not os.path.isfile(self.testfile + ".bz2"):
            with fabioutils.BZ2File(self.testfile + ".bz2", "wb") as wf:
                wf.write(b"{ hello }")
        self.obj = FabioImage()

    def testFlat(self):
        """no compression"""
        res = self.obj._open(self.testfile)
        self.assertEqual(res.read(), b"{ hello }")
        res.close()

    def testgz(self):
        """gzipped"""
        res = self.obj._open(self.testfile + ".gz")
        self.assertEqual(res.read(), b"{ hello }")
        res.close()

    def testbz2(self):
        """bzipped"""
        res = self.obj._open(self.testfile + ".bz2")
        self.assertEqual(res.read(), b"{ hello }")
        res.close()

    def test_badtype(self):
        self.assertRaises(TypeError, self.obj._open, None)

    def test_pathlib(self):
        if pathlib is None:
            self.skipTest("pathlib is not available")
        path = pathlib.PurePath(self.testfile + ".bz2")
        res = self.obj._open(path)
        self.assertIsNotNone(res)
        res.close()


@unittest.skipIf(lzma is None, "lzma is not available")
class TestXZ(unittest.TestCase):
    """Transparent XZ compression of detector images (#648)."""

    def setUp(self):
        directory = tempfile.TemporaryDirectory(dir=UtilsTest.tempdir)
        self.addCleanup(directory.cleanup)
        self.directory = directory.name
        self.data = numpy.arange(12, dtype=numpy.uint16).reshape(3, 4)

    def test_bug_648(self):
        """Read an EDF compressed independently with the standard library."""
        plain = os.path.join(self.directory, "image.edf")
        compressed = plain + ".xz"
        EdfImage(data=self.data, header={"Title": "XZ image"}).write(plain)
        with open(plain, "rb") as stream:
            payload = stream.read()
        with lzma.open(compressed, "wb") as stream:
            stream.write(payload)
        with openimage(compressed) as image:
            numpy.testing.assert_array_equal(image.data, self.data)
            self.assertEqual(image.header["Title"], "XZ image")

    def test_cbf_read(self):
        plain = os.path.join(self.directory, "image.cbf")
        data = self.data.astype(numpy.int32) - 5
        CbfImage(data=data).write(plain)
        with open(plain, "rb") as source, lzma.open(plain + ".xz", "wb") as target:
            target.write(source.read())
        with openimage(plain + ".xz") as image:
            numpy.testing.assert_array_equal(image.data, data)

    def test_edf_write(self):
        filename = os.path.join(self.directory, "image.edf.xz")
        EdfImage(data=self.data, header={"Title": "XZ image"}).write(filename)
        with open(filename, "rb") as stream:
            compressed = stream.read()
        self.assertTrue(compressed.startswith(b"\xfd7zXZ\x00"))
        # Use an independent decompressor, not a round-trip through XZFile.
        with openimage(fabioutils.BytesIO(lzma.decompress(compressed))) as image:
            numpy.testing.assert_array_equal(image.data, self.data)
            self.assertEqual(image.header["Title"], "XZ image")

    def test_multiframe(self):
        filename = os.path.join(self.directory, "frames.edf.xz")
        image = EdfImage(data=self.data, header={"Frame": "0"})
        for index in range(1, 3):
            image.append_frame(data=self.data + index, header={"Frame": str(index)})
        image.write(filename)
        with openimage(filename) as image:
            self.assertEqual(image.nframes, 3)
            for index in (2, 0, 1):
                frame = image.get_frame(index)
                numpy.testing.assert_array_equal(frame.data, self.data + index)
                self.assertEqual(frame.header["Frame"], str(index))
        with openheader(filename) as header:
            self.assertEqual(header.header["Frame"], "0")

    def test_numbered_series(self):
        filenames = [os.path.join(self.directory, f"image_{i:04d}.edf.xz") for i in range(2)]
        for index, filename in enumerate(filenames):
            EdfImage(data=self.data + index).write(filename)
        name = fabioutils.FilenameObject(filename=filenames[0])
        self.assertEqual(name.num, 0)
        self.assertIn("edf", name.format)
        self.assertEqual(name.tostring(), filenames[0])
        self.assertEqual(fabioutils.next_filename(filenames[0]), filenames[1])
        self.assertEqual(fabioutils.previous_filename(filenames[1]), filenames[0])
        with openimage(name) as first, first.next() as second:
            numpy.testing.assert_array_equal(second.data, self.data + 1)
        with open_series(filenames=filenames) as series:
            frames = [frame.data.copy() for frame in series.frames()]
        self.assertEqual(len(frames), 2)
        for index, data in enumerate(frames):
            numpy.testing.assert_array_equal(data, self.data + index)

    def test_stream_metadata_and_position(self):
        filename = os.path.join(self.directory, "data.xz")
        payload = b"FabIO compressed stream" * 10
        with lzma.open(filename, "wb") as stream:
            stream.write(payload)
        with FabioImage()._open(pathlib.Path(filename)) as stream:
            self.assertEqual(stream.name, filename)
            self.assertEqual(stream.mode, "rb")
            self.assertTrue(stream.lock.acquire(blocking=False))
            stream.lock.release()
            self.assertEqual(stream.read(7), payload[:7])
            self.assertEqual(stream.size, len(payload))
            self.assertEqual(stream.tell(), 7)
            self.assertEqual(stream.read(), payload[7:])
            stream.seek(0)
            self.assertEqual(stream.read(), payload)
        self.assertTrue(stream.closed)
        with self.assertRaises(ValueError):
            stream.read(1)

    def test_write_size(self):
        filename = os.path.join(self.directory, "data.xz")
        with FabioImage()._open(filename, "wb") as stream:
            stream.write(b"abc")
            self.assertEqual(stream.size, 3)
            stream.write(b"def")
            self.assertEqual(stream.size, 6)
        with lzma.open(filename, "rb") as stream:
            self.assertEqual(stream.read(), b"abcdef")

    def test_codec_stream_requirements(self):
        filename = os.path.join(self.directory, "data.xz")
        payload = b"{ decompressed data }"
        with lzma.open(filename, "wb") as stream:
            stream.write(payload)
        for flag in ("_need_a_seek_to_read", "_need_a_real_file"):
            with self.subTest(flag=flag):
                image = FabioImage()
                setattr(image, flag, True)
                stream = image._open(filename)
                try:
                    self.assertEqual(stream.read(), payload)
                    stream.seek(2)
                    self.assertEqual(stream.read(4), payload[2:6])
                    if flag == "_need_a_real_file":
                        temporary_name = stream.name
                        self.assertTrue(os.path.isfile(temporary_name))
                finally:
                    stream.close()
                if flag == "_need_a_real_file":
                    self.assertFalse(os.path.exists(temporary_name))

    def test_invalid_stream(self):
        filename = os.path.join(self.directory, "broken.xz")
        for data, error in ((b"not an XZ stream", lzma.LZMAError),
                            (lzma.compress(b"payload")[:-12], EOFError)):
            with self.subTest(error=error):
                with open(filename, "wb") as stream:
                    stream.write(data)
                with FabioImage()._open(filename) as stream, self.assertRaises(error):
                    stream.read()

    def test_missing_lzma(self):
        filename = os.path.join(self.directory, "missing.edf.xz")
        with mock.patch.object(fabioutils, "XZFile", None):
            for mode in ("rb", "wb"):
                with self.subTest(mode=mode), self.assertRaisesRegex(OSError, "lzma"):
                    FabioImage()._open(filename, mode)
        self.assertFalse(os.path.exists(filename))

    def test_ge_extension_detection(self):
        # GE files can have an EDF header; preserve the extension discriminator.
        for suffix in ("", ".gz", ".bz2", ".xz", ".zst"):
            with self.subTest(suffix=suffix):
                self.assertEqual(_do_magic(b"{\n", "image.edf.ge5" + suffix), "GE")
                self.assertEqual(_do_magic(b"{\n", "image.edf" + suffix), "edf")


class TestZstandard(unittest.TestCase):
    """Transparent Zstandard compression of detector images (#648)."""

    def setUp(self):
        directory = tempfile.TemporaryDirectory(dir=UtilsTest.tempdir)
        self.addCleanup(directory.cleanup)
        self.directory = pathlib.Path(directory.name)
        self.data = numpy.arange(12, dtype=numpy.uint16).reshape(3, 4)

    def _backend(self):
        try:
            from compression import zstd
        except ImportError:
            try:
                from backports import zstd
            except ImportError:
                self.skipTest("Zstandard is not available")
        return zstd

    def test_bug_648_zstd(self):
        backend = self._backend()
        plain = self.directory / "image.edf"
        compressed = self.directory / "image.edf.zst"
        EdfImage(data=self.data, header={"Title": "Zstandard image"}).write(plain)
        compressed.write_bytes(backend.compress(plain.read_bytes()))
        with openimage(compressed) as image:
            numpy.testing.assert_array_equal(image.data, self.data)
            self.assertEqual(image.header["Title"], "Zstandard image")

    def test_edf_write_and_frame_seeking(self):
        backend = self._backend()
        compressed = self.directory / "frames.edf.zst"
        image = EdfImage(data=self.data, header={"Frame": "0"})
        image.append_frame(data=self.data + 1, header={"Frame": "1"})
        image.write(compressed)
        payload = compressed.read_bytes()
        self.assertTrue(payload.startswith(b"\x28\xb5\x2f\xfd"))
        with openimage(fabioutils.BytesIO(backend.decompress(payload))) as image:
            numpy.testing.assert_array_equal(image.get_frame(1).data, self.data + 1)
        with openimage(compressed) as image, openheader(compressed) as header:
            self.assertEqual(image.nframes, 2)
            self.assertEqual(header.header["Frame"], "0")
            for index in (1, 0):
                numpy.testing.assert_array_equal(image.get_frame(index).data, self.data + index)

    def test_numbered_series(self):
        self._backend()
        filenames = [str(self.directory / f"image_{index:04d}.edf.zst") for index in range(2)]
        for index, filename in enumerate(filenames):
            EdfImage(data=self.data + index).write(filename)
        name = fabioutils.FilenameObject(filename=filenames[0])
        self.assertEqual(name.num, 0)
        self.assertEqual(name.tostring(), filenames[0])
        self.assertEqual(fabioutils.next_filename(filenames[0]), filenames[1])
        with openimage(name) as first, first.next() as second:
            numpy.testing.assert_array_equal(second.data, self.data + 1)

    def test_stream_metadata_and_size(self):
        backend = self._backend()
        compressed = self.directory / "data.zst"
        data = b"compressed data" * 16
        with FabioImage()._open(compressed, "wb") as stream:
            stream.write(data)
            self.assertEqual(stream.size, len(data))
        self.assertEqual(backend.decompress(compressed.read_bytes()), data)
        with FabioImage()._open(compressed) as stream:
            self.assertEqual(stream.name, str(compressed))
            self.assertEqual(stream.mode, "rb")
            self.assertTrue(stream.lock.acquire(blocking=False))
            stream.lock.release()
            self.assertEqual(stream.read(7), data[:7])
            self.assertEqual(stream.size, len(data))
            self.assertEqual(stream.tell(), 7)
            self.assertEqual(stream.read(), data[7:])

    def test_unavailable_backend(self):
        compressed = self.directory / "missing.edf.zst"
        with mock.patch.object(fabioutils, "ZstdFile", None):
            for mode in ("rb", "wb"):
                with self.subTest(mode=mode), self.assertRaisesRegex(OSError, "backports.zstd"):
                    FabioImage()._open(compressed, mode)
        self.assertFalse(compressed.exists())


class TestPilImage(unittest.TestCase):
    """check PIL creation"""

    def setUp(self):
        if pilutils.Image is None:
            self.skipTest("PIL is not available")

        """ list of working numeric types"""
        self.okformats = [
            numpy.uint8,
            numpy.int8,
            numpy.uint16,
            numpy.int16,
            numpy.uint32,
            numpy.int32,
            numpy.float32,
        ]

    def mkdata(self, shape, typ):
        """generate [01] testdata"""
        return (numpy.random.random(shape)).astype(typ)

    def testpil(self):
        for typ in self.okformats:
            for shape in [(10, 20), (431, 1325)]:
                testdata = self.mkdata(shape, typ)
                img = FabioImage(testdata, {"title": "Random data"})
                pim = img.toPIL16()
                for i in [0, 5, 6, shape[1] - 1]:
                    for j in [0, 5, 7, shape[0] - 1]:
                        errstr = str(typ) + f" {i} {j} {testdata[j, i]:f} {pim.getpixel((i, j)):f} t={typ}"

                        er1 = img.data[j, i] - pim.getpixel((i, j))
                        er2 = img.data[j, i] + pim.getpixel((i, j))

                        # difference as % error in case of rounding
                        if er2 != 0.0:
                            err = er1 / er2
                        else:
                            err = er1

                        self.assertAlmostEqual(err, 0, 6, errstr)


class TestPilImage2(TestPilImage):
    """check with different numbers"""

    def mkdata(self, shape, typ):
        """positive and big"""
        if numpy.issubdtype(typ, numpy.integer):
            maxi = numpy.iinfo(typ).max
        else:
            maxi = numpy.iinfo(int).max
        return (numpy.random.random(shape) * (0.1 * maxi)).astype(typ)


class TestPilImage3(TestPilImage):
    """check with different numbers"""

    def mkdata(self, shape, typ):
        """positive, negative and big"""
        if numpy.issubdtype(typ, numpy.integer):
            maxi = numpy.iinfo(typ).max
        else:
            maxi = numpy.iinfo(int).max
        return ((numpy.random.random(shape) - 0.5) * (0.1 * maxi)).astype(typ)


class TestDeprecatedFabioImage(unittest.TestCase):
    def test_patch_dim(self):
        data = numpy.array(numpy.arange(3 * 10)).reshape(3, 10)
        image = FabioImage(data=data)
        # Usecase found in some projects
        image.dim2, image.dim1 = data.shape
        # It should not change anything
        self.assertEqual(image.shape, data.shape)

    def test_cleanup_pilimage_cache(self):
        data = numpy.array(numpy.arange(3 * 10)).reshape(3, 10)
        image = FabioImage(data=data)
        # It was a way to force clean up of the cache
        image.pilimage = None


class TestFabioImage(unittest.TestCase):
    def test_iter_abort_iteration(self):
        data = numpy.zeros((2, 2))
        image = FabioImage(data=data)
        for frame in image:
            self.assertEqual(frame.data[0, 0], 0)

class TestSexedDtype(unittest.TestCase):
    def test_sexed_dtypes(self):
        a = FabioImage.get_stype("float32", ">")
        self.assertEqual(a.str, ">f4")
        a = FabioImage.get_stype("float64", "<")
        self.assertEqual(a.str, "<f8")
        a = FabioImage.get_stype(numpy.float32, "big")
        self.assertEqual(a.str, ">f4")
        a = FabioImage.get_stype(numpy.float64, "little")
        self.assertEqual(a.str, "<f8")

def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestFabioImage))
    testsuite.addTest(loadTests(Test50000))
    testsuite.addTest(loadTests(TestSlices))
    testsuite.addTest(loadTests(TestOpen))
    testsuite.addTest(loadTests(TestXZ))
    testsuite.addTest(loadTests(TestZstandard))
    testsuite.addTest(loadTests(TestPilImage))
    testsuite.addTest(loadTests(TestPilImage2))
    testsuite.addTest(loadTests(TestPilImage3))
    testsuite.addTest(loadTests(TestDeprecatedFabioImage))
    testsuite.addTest(loadTests(TestSexedDtype))
    return testsuite


if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite())
