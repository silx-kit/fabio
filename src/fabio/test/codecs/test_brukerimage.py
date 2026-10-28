#!/usr/bin/env python
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
#bruker Unit tests

#built on testbrukerimage
19/01/2015
"""

import logging
import os
import unittest

import numpy

from ... import fabioutils
from ...brukerimage import brukerimage
from ..utilstest import UtilsTest

logger = logging.getLogger(__name__)

# this is actually a violation of the bruker format since the order of
# the header items is specified
# in the standard, whereas the order of a python dictionary is not
MYHEADER = {
    "FORMAT": "86",
    "NPIXELB": "2",
    "VERSION": "9",
    "HDRBLKS": "5",
    "NOVERFL": "4",
    "NCOLS": "256",
    "NROWS": "256",
    "WORDORD": "0",
}

MYIMAGE = numpy.ones((256, 256), numpy.uint16) * 16
MYIMAGE[0, 0] = 0
MYIMAGE[1, 1] = 32
MYIMAGE[127:129, 127:129] = 65535
if not numpy.little_endian:
    MYIMAGE.byteswap(True)

OVERFLOWS = [
    [f"{4194304:09d}", f"{127 * 256 + 127:07d}"],
    [f"{4194304:09d}", f"{127 * 256 + 128:07d}"],
    [f"{4194304:09d}", f"{128 * 256 + 127:07d}"],
    [f"{4194304:09d}", f"{128 * 256 + 128:07d}"],
]


class TestBruker(unittest.TestCase):
    """basic test"""

    def setUp(self):
        """Generate a test bruker image"""
        self.filename = os.path.join(UtilsTest.tempdir, "image.0000")

        with open(self.filename, "wb") as fout:
            wrb = 0
            for key, val in MYHEADER.items():
                fout.write((f"{key:<7}" + ":" + f"{val:<72}").encode("ASCII"))
                wrb = wrb + 80
            hdrblks = int(MYHEADER["HDRBLKS"])
            while wrb < hdrblks * 512:
                fout.write(b"\x1a\x04")
                fout.write(b"." * 78)
                wrb = wrb + 80
            fout.write(MYIMAGE.tobytes())

            noverfl = int(MYHEADER["NOVERFL"])
            fout.writelines((ovf[0] + ovf[1]).encode("ASCII") for ovf in OVERFLOWS)
            fout.write(b"." * (512 - (16 * noverfl) % 512))

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        if os.path.exists(self.filename):
            os.unlink(self.filename)

    def test_read(self):
        """see if we can read the test image"""
        obj = brukerimage()
        obj.read(self.filename)
        self.assertAlmostEqual(obj.getmean(), 272.0, 2)
        self.assertEqual(obj.getmin(), 0)
        self.assertEqual(obj.getmax(), 4194304)


class TestBzipBruker(TestBruker):
    """test for a bzipped image"""

    def setUp(self):
        """create the image"""
        TestBruker.setUp(self)
        if os.path.isfile(self.filename + ".bz2"):
            os.unlink(self.filename + ".bz2")
        with fabioutils.BZ2File(self.filename + ".bz2", "wb") as wf, open(self.filename, "rb") as rf:
            wf.write(rf.read())
        self.filename = self.filename + ".bz2"


class TestGzipBruker(TestBruker):
    """test for a gzipped image"""

    def setUp(self):
        """Create the image"""
        TestBruker.setUp(self)
        if os.path.isfile(self.filename + ".gz"):
            os.unlink(self.filename + ".gz")
        with fabioutils.GzipFile(self.filename + ".gz", "wb") as wf, open(self.filename, "rb") as rf:
            wf.write(rf.read())
        self.filename = self.filename + ".gz"


class TestBrukerLinear(unittest.TestCase):
    """basic test, test a random array of float32"""

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.filename = os.path.join(UtilsTest.tempdir, "bruker.0000")
        self.data = numpy.random.random((500, 550)).astype("float32")

    def test_linear(self):
        """test for self consistency of random data read/write"""
        obj = brukerimage(data=self.data)
        obj.write(self.filename)
        new = brukerimage()
        new.read(self.filename)
        error = abs(new.data - self.data).max()
        self.assertTrue(
            error < numpy.finfo(numpy.float32).eps, f"Error is {error}>1e-7"
        )

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        if os.path.exists(self.filename):
            os.unlink(self.filename)


class TestBrukerOverflow(unittest.TestCase):
    """The overflow table must be counted in NOVERFL when writing new data"""

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.filename = os.path.join(UtilsTest.tempdir, "overflow.0000")

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        if os.path.exists(self.filename):
            os.unlink(self.filename)

    def test_integer(self):
        data = numpy.zeros((64, 64), dtype=numpy.int32)
        data[3, 5] = 70000
        data[10, 10] = 300
        brukerimage(data=data).write(self.filename)
        new = brukerimage()
        new.read(self.filename)
        self.assertEqual(new.header["NOVERFL"], "2")
        self.assertEqual(abs(new.data - data).max(), 0)

    def test_float(self):
        data = numpy.linspace(0, 1000, 84, dtype=numpy.float32).reshape(7, 12)
        brukerimage(data=data).write(self.filename)
        new = brukerimage()
        new.read(self.filename)
        self.assertLess(abs(new.data - data).max(), 1e-3)

    def test_float_below_offset(self):
        """values below the LINEAR offset are clipped to the offset, not wrapped"""
        data = numpy.linspace(-100, 1000, 84, dtype=numpy.float32).reshape(7, 12)
        brukerimage(data=data, header={"LINEAR": "0.5 10"}).write(self.filename)
        new = brukerimage()
        new.read(self.filename)
        expected = numpy.maximum(data, 10)
        self.assertLess(abs(new.data - expected).max(), 0.5)

    def test_float_above_range(self):
        """values above the uint32 range are clipped, not wrapped"""
        data = numpy.full((128, 128), 1e10, dtype=numpy.float32)
        brukerimage(data=data, header={"LINEAR": "1.0 0.0"}).write(self.filename)
        new = brukerimage()
        new.read(self.filename)
        self.assertEqual(int(new.header["NPIXELB"]), 4)
        self.assertEqual(new.header["NOVERFL"], "0")
        self.assertTrue(numpy.allclose(new.data, 2**32 - 2))

    def test_integer_stale_linear(self):
        """a LINEAR scaling inherited from a float frame must not be applied to integers"""
        data = numpy.arange(84, dtype=numpy.int32).reshape(7, 12)
        brukerimage(data=data, header={"LINEAR": "0.5 10"}).write(self.filename)
        new = brukerimage()
        new.read(self.filename)
        self.assertEqual(abs(new.data - data).max(), 0)

    def test_integer_negative(self):
        """negative integers are clipped to 0, not wrapped"""
        data = numpy.arange(-42, 42, dtype=numpy.int32).reshape(7, 12)
        brukerimage(data=data).write(self.filename)
        new = brukerimage()
        new.read(self.filename)
        self.assertEqual(new.header["NOVERFL"], "0")
        self.assertEqual(abs(new.data - numpy.maximum(data, 0)).max(), 0)

    def test_gen_overflow_float(self):
        """gen_overflow without argument works on float data"""
        data = numpy.linspace(0, 1000, 84, dtype=numpy.float32).reshape(7, 12)
        overflow = brukerimage(data=data).gen_overflow()
        self.assertEqual(len(overflow.rstrip(".")), 16 * 83)

    def test_gen_overflow_data(self):
        """gen_overflow uses the bpp of the data it is given"""
        img = brukerimage(data=numpy.zeros((128, 128), dtype=numpy.float32))
        overflow = img.gen_overflow(numpy.full((128, 128), 300, dtype=numpy.int32))
        self.assertEqual(overflow.rstrip("."), "")

    def test_fortran_order(self):
        """overflow positions follow the C order of the file, whatever the memory layout"""
        data = numpy.zeros((7, 12), dtype=numpy.int32)
        data[1, 2] = 300
        data[5, 0] = 70000
        brukerimage(data=numpy.asfortranarray(data)).write(self.filename)
        new = brukerimage()
        new.read(self.filename)
        self.assertEqual(new.header["NOVERFL"], "2")
        self.assertEqual(abs(new.data - data).max(), 0)

    def test_failed_write_keeps_header(self):
        """the header is left untouched when the file cannot be written"""
        data = numpy.full((7, 12), 300, dtype=numpy.int32)
        header = {"LINEAR": "0.5 10", "NPIXELB": "4"}
        img = brukerimage(data=data, header=header)
        filename = os.path.join(UtilsTest.tempdir, "missing_dir", "overflow.0000")
        with self.assertRaises(OSError):
            img.write(filename)
        self.assertEqual(dict(img.header), header)

    def test_overflow_value_too_large(self):
        """overflow values beyond 9 digits use a larger bpp instead"""
        data = numpy.zeros((7, 12), dtype=numpy.int32)
        data[1, 2] = 1_500_000_000
        brukerimage(data=data).write(self.filename)
        new = brukerimage()
        new.read(self.filename)
        self.assertEqual(int(new.header["NPIXELB"]), 4)
        self.assertEqual(abs(new.data - data).max(), 0)

    def test_overflow_position_too_large(self):
        """overflow positions beyond 7 digits use a larger bpp instead"""
        data = numpy.zeros((3200, 3200), dtype=numpy.uint16)
        data[-1, -1] = 300
        brukerimage(data=data).write(self.filename)
        new = brukerimage()
        new.read(self.filename)
        self.assertEqual(int(new.header["NPIXELB"]), 2)
        self.assertEqual(abs(new.data - data).max(), 0)

    def test_overflow_not_storable(self):
        """values beyond the uint32 range cannot be stored at all"""
        data = numpy.zeros((7, 12), dtype=numpy.int64)
        data[1, 2] = 5_000_000_000
        img = brukerimage(data=data)
        with self.assertRaises(ValueError):
            img.write(self.filename)
        self.assertFalse(os.path.exists(self.filename))
        self.assertNotIn("NOVERFL", img.header)

    def test_rewrite(self):
        """bpp must be recalculated when the data changes between two writes"""
        img = brukerimage(data=numpy.zeros((128, 128), dtype=numpy.int32))
        img.write(self.filename)
        data = numpy.full((128, 128), 300, dtype=numpy.int32)
        img.data = data
        img.write(self.filename)
        new = brukerimage()
        new.read(self.filename)
        self.assertEqual(int(new.header["NPIXELB"]), 2)
        self.assertEqual(new.header["NOVERFL"], "0")
        self.assertEqual(abs(new.data - data).max(), 0)


# statistics come from fit2d I think
# filename dim1 dim2 min max mean stddev
TESTIMAGES = """Cr8F8140k103.0026   512  512  0  145942 289.37  432.17
                Cr8F8140k103.0026.gz   512  512  0  145942 289.37  432.17
                Cr8F8140k103.0026.bz2   512  512  0 145942 289.37  432.17"""


class TestRealImg(unittest.TestCase):
    """check some read data from bruker detector"""

    def setUp(self):
        """
        download images
        """
        self.im_dir = os.path.dirname(UtilsTest.getimage("Cr8F8140k103.0026.bz2"))

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        self.im_dir = None

    def test_read(self):
        """check we can read bruker images"""
        for line in TESTIMAGES.split("\n"):
            vals = line.split()
            name = vals[0]
            dim1, dim2 = [int(x) for x in vals[1:3]]
            shape = dim2, dim1
            mini, maxi, mean, stddev = [float(x) for x in vals[3:]]
            obj = brukerimage()
            obj.read(os.path.join(self.im_dir, name))
            self.assertAlmostEqual(mini, obj.getmin(), 2, "getmin")
            self.assertAlmostEqual(maxi, obj.getmax(), 2, "getmax")
            self.assertAlmostEqual(mean, obj.getmean(), 2, "getmean")
            self.assertAlmostEqual(stddev, obj.getstddev(), 2, "getstddev")
            self.assertEqual(shape, obj.shape)

    def test_write(self):
        "Test writing with self consistency at the fabio level"
        for line in TESTIMAGES.split("\n"):
            vals = line.split()
            name = vals[0]
            obj = brukerimage()
            ref = brukerimage()
            fname = os.path.join(self.im_dir, name)
            obj.read(fname)
            obj.write(os.path.join(UtilsTest.tempdir, name))
            other = brukerimage()
            other.read(os.path.join(UtilsTest.tempdir, name))
            ref.read(fname)
            self.assertEqual(abs(obj.data - other.data).max(), 0, "data are the same")
            for key in ref.header:
                if key in ("filename",):
                    continue
                if key not in other.header:
                    logger.warning(
                        "Key %s is missing in new header, was %s",
                        key,
                        ref.header[key],
                    )
                else:
                    self.assertEqual(
                        ref.header[key],
                        other.header[key],
                        f"value are the same for key {key}: was {ref.header[key]} now {other.header[key]}",
                    )


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestBruker))
    testsuite.addTest(loadTests(TestBzipBruker))
    testsuite.addTest(loadTests(TestGzipBruker))
    testsuite.addTest(loadTests(TestRealImg))
    testsuite.addTest(loadTests(TestBrukerLinear))
    testsuite.addTest(loadTests(TestBrukerOverflow))
    return testsuite


if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite())
