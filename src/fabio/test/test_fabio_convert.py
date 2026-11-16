#!/usr/bin/env python
#
#    Project: Fable Input Output
#             https://github.com/silx-kit/fabio
#
#    Copyright (C) European Synchrotron Radiation Facility, Grenoble, France
#
#    Principal author:       Valentin Valls (valentin.valls@esrf.fr)
#
"""
Test for fabio-convert
"""

import logging
import hashlib
import os.path
import shutil
import subprocess
import sys
import time
import unittest

import numpy

import fabio.app.convert

from .utilstest import UtilsTest

_logger = logging.getLogger(__name__)


class TestFabioConvert(unittest.TestCase):
    def create_test_env(self):
        path = os.path.join(UtilsTest.tempdir, self.id())
        os.makedirs(path)
        os.mkdir(os.path.join(path, "input"))
        os.mkdir(os.path.join(path, "output"))

        data = numpy.random.rand(100, 100)
        image = fabio.edfimage.edfimage(data=data)
        image.write(os.path.join(path, "input", "01.edf"))

        data = numpy.random.rand(100, 100)
        image = fabio.edfimage.edfimage(data=data)
        image.write(os.path.join(path, "input", "02.edf"))

        data = numpy.random.rand(100, 100)
        image = fabio.edfimage.edfimage(data=data)
        image.write(os.path.join(path, "input", "03.edf"))

        data = numpy.random.rand(100, 100)
        image = fabio.edfimage.edfimage(data=data)
        # it is not the right file format, but it makes no difference
        image.write(os.path.join(path, "output", "01.msk"))

        data = numpy.random.rand(100, 100)
        image = fabio.edfimage.edfimage(data=data)
        # it is not the right file format, but it makes no difference
        image.write(os.path.join(path, "output", "02.msk"))

        t = time.time()
        older = (t - 5000, t - 5000)
        default = (t - 4000, t - 4000)
        newer = (t - 3000, t - 3000)

        os.utime(os.path.join(path, "input", "01.edf"), default)
        os.utime(os.path.join(path, "input", "02.edf"), default)
        os.utime(os.path.join(path, "input", "03.edf"), default)
        os.utime(os.path.join(path, "output", "01.msk"), older)
        os.utime(os.path.join(path, "output", "02.msk"), newer)

        return path

    def clean_test_env(self, path):
        shutil.rmtree(path)

    def setUp(self):
        self.__oldPath = os.getcwd()
        self.__testPath = self.create_test_env()
        os.chdir(self.__testPath)
        env = {str(k): str(v) for k, v in os.environ.items()}
        env["PYTHONPATH"] = os.pathsep.join(sys.path)
        self.__env = env
        self.__script = fabio.app.convert.__file__

    def tearDown(self):
        os.chdir(self.__oldPath)
        self.clean_test_env(self.__testPath)
        self.exe, self.env = None, None

    def subprocessFabioConvert(self, *args):
        commandLine = [sys.executable, self.__script]
        commandLine.extend(args)
        _logger.info("Execute: %s", " ".join(commandLine))
        p = subprocess.Popen(
            commandLine,
            env=self.__env,
            shell=False,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return p

    def logCommunicate(self, p):
        out, err = p.communicate()
        _logger.info("Return code: %d", p.returncode)
        if p.returncode != 0:
            _logger.info("stdout:")
            _logger.info("%s", out)
            _logger.info("stderr:")
            _logger.info("%s", err)
        else:
            _logger.debug("stdout:")
            _logger.debug("%s", out)
            _logger.debug("stderr:")
            _logger.debug("%s", err)

    def testSingleFile(self):
        p = self.subprocessFabioConvert("input/03.edf", "-o=output/03.msk")
        self.logCommunicate(p)
        assert os.path.exists("output/03.msk")
        image = fabio.open("output/03.msk")
        assert isinstance(image, fabio.fit2dmaskimage.Fit2dMaskImage)
        assert image.data.shape == (100, 100)

    def testSingleFileToDir(self):
        p = self.subprocessFabioConvert("input/03.edf", "-F=msk", "-o=output")
        self.logCommunicate(p)
        assert os.path.exists("output/03.msk")

    def testSingleFileWithWildcardToDir(self):
        p = self.subprocessFabioConvert("input/03.*", "-F=msk", "-o=output")
        self.logCommunicate(p)
        assert os.path.exists("output/03.msk")

    def testFullFormatName(self):
        p = self.subprocessFabioConvert("input/03.*", "-F=numpyimage", "-o=output")
        self.logCommunicate(p)
        assert os.path.exists("output/03.npy")
        image = fabio.open("output/03.npy")
        assert isinstance(image, fabio.numpyimage.NumpyImage)
        assert image.data.shape == (100, 100)

    def testForceOption(self):
        date1 = os.path.getmtime("output/01.msk")
        date2 = os.path.getmtime("output/02.msk")
        p = self.subprocessFabioConvert("input/*.edf", "-f", "-F=msk", "-o=output")
        self.logCommunicate(p)
        assert os.path.exists("output/01.msk")
        assert date1 < os.path.getmtime("output/01.msk")
        assert os.path.exists("output/02.msk")
        assert date2 < os.path.getmtime("output/02.msk")
        assert os.path.exists("output/03.msk")

    def testRemoveDestinationOption(self):
        date1 = os.path.getmtime("output/01.msk")
        date2 = os.path.getmtime("output/02.msk")
        p = self.subprocessFabioConvert(
            "input/*.edf", "--remove-destination", "-F=msk", "-o=output"
        )
        self.logCommunicate(p)
        assert os.path.exists("output/01.msk")
        assert date1 < os.path.getmtime("output/01.msk")
        assert os.path.exists("output/02.msk")
        assert date2 < os.path.getmtime("output/02.msk")
        assert os.path.exists("output/03.msk")

    def testNoClobberOption(self):
        date1 = os.path.getmtime("output/01.msk")
        date2 = os.path.getmtime("output/02.msk")
        p = self.subprocessFabioConvert("input/*.edf", "-n", "-F=msk", "-o=output")
        self.logCommunicate(p)
        assert os.path.exists("output/01.msk")
        assert date1 == os.path.getmtime("output/01.msk")
        assert os.path.exists("output/02.msk")
        assert date2 == os.path.getmtime("output/02.msk")
        assert os.path.exists("output/03.msk")

    def testUpdateOption(self):
        date1 = os.path.getmtime("output/01.msk")
        date2 = os.path.getmtime("output/02.msk")
        p = self.subprocessFabioConvert(
            "input/*.edf", "--update", "-F=msk", "-o=output"
        )
        self.logCommunicate(p)
        assert os.path.exists("output/01.msk")
        assert date1 < os.path.getmtime("output/01.msk")
        assert os.path.exists("output/02.msk")
        assert date2 == os.path.getmtime("output/02.msk")
        assert os.path.exists("output/03.msk")

    def testDefaultOption(self):
        date1 = os.path.getmtime("output/01.msk")
        date2 = os.path.getmtime("output/02.msk")
        p = self.subprocessFabioConvert("input/*.edf", "-F=msk", "-o=output")
        p.stdin.write(b"yes\n")
        p.stdin.write(b"no\n")
        self.logCommunicate(p)
        assert os.path.exists("output/01.msk")
        assert date1 < os.path.getmtime("output/01.msk")
        assert os.path.exists("output/02.msk")
        assert date2 == os.path.getmtime("output/02.msk")
        assert os.path.exists("output/03.msk")

    def testInteractiveOption(self):
        date1 = os.path.getmtime("output/01.msk")
        date2 = os.path.getmtime("output/02.msk")
        p = self.subprocessFabioConvert(
            "input/*.edf", "-n", "-i", "-F=msk", "-o=output"
        )
        p.stdin.write(b"yes\n")
        p.stdin.write(b"no\n")
        self.logCommunicate(p)
        assert os.path.exists("output/01.msk")
        assert date1 < os.path.getmtime("output/01.msk")
        assert os.path.exists("output/02.msk")
        assert date2 == os.path.getmtime("output/02.msk")
        assert os.path.exists("output/03.msk")

    def create_stack(self, filename="input/stack.edf"):
        """Small synthetic detector stack for the split request in #449."""
        arrays = [numpy.arange(12).reshape(3, 4).astype("int32") + i * 100
                  for i in range(3)]
        image = fabio.edfimage.EdfImage(
            data=arrays[0], header={"FrameLabel": "frame-0"}
        )
        for i, data in enumerate(arrays[1:], 1):
            image.append_frame(data=data, header={"FrameLabel": f"frame-{i}"})
        image.write(filename)
        return arrays

    def run_split(self, *args, answers=None, expected=0):
        process = self.subprocessFabioConvert("--split", *args)
        out, err = process.communicate(input=answers, timeout=30)
        self.assertEqual(process.returncode, expected, (out, err))
        self.assertNotIn(b"Traceback", err)
        return err

    def test_split_449_frames_and_headers(self):
        arrays = self.create_stack()
        with open("input/stack.edf", "rb") as stream:
            original = hashlib.sha256(stream.read()).digest()
        self.run_split("input/stack.edf", "-F=edf")
        for i, data in enumerate(arrays):
            with fabio.open(f"input/stack_{i:04d}.edf") as image:
                self.assertEqual(image.nframes, 1)
                numpy.testing.assert_array_equal(image.data, data)
                self.assertEqual(image.header["FrameLabel"], f"frame-{i}")
        with open("input/stack.edf", "rb") as stream:
            self.assertEqual(hashlib.sha256(stream.read()).digest(), original)

    def test_split_449_output_file_and_directory(self):
        arrays = self.create_stack()
        self.run_split("input/stack.edf", "-o=output/custom.npy")
        self.run_split("input/stack.edf", "-F=edf", "-o=output")
        for i, data in enumerate(arrays):
            numpy.testing.assert_array_equal(
                numpy.load(f"output/custom_{i:04d}.npy"), data
            )
            with fabio.open(f"output/stack_{i:04d}.edf") as image:
                numpy.testing.assert_array_equal(image.data, data)

    def test_split_449_tiff_and_hdf5(self):
        arrays = self.create_stack()
        from fabio.TiffIO import TiffIO
        with open("input/stack.tif", "w+b") as stream:
            tiff = TiffIO(stream, mode="w")
            for data in arrays:
                tiff.writeImage(data)
        from fabio.eigerimage import EigerImage
        EigerImage(data=numpy.stack(arrays)).write("input/stack.h5")
        for source in ("input/stack.tif", "input/stack.h5"):
            with self.subTest(source=source):
                self.run_split(source, "-F=npy", "-o=output", "-f")
                for i, data in enumerate(arrays):
                    numpy.testing.assert_array_equal(
                        numpy.load(f"output/stack_{i:04d}.npy"), data
                    )

    def test_split_449_no_clobber_and_dry_run(self):
        arrays = self.create_stack()
        target = "output/stack_0000.npy"
        numpy.save(target, numpy.array([42]))
        self.run_split("input/stack.edf", "-F=npy", "-o=output", "-n", "--dry-run")
        self.assertFalse(os.path.exists("output/stack_0001.npy"))
        numpy.testing.assert_array_equal(numpy.load(target), [42])
        self.run_split("input/stack.edf", "-F=npy", "-o=output", "-n")
        numpy.testing.assert_array_equal(numpy.load(target), [42])
        numpy.testing.assert_array_equal(numpy.load("output/stack_0002.npy"), arrays[2])

    def test_split_449_interactive_and_update(self):
        arrays = self.create_stack()
        for i in range(2):
            numpy.save(f"output/stack_{i:04d}.npy", numpy.array([42]))
        self.run_split("input/stack.edf", "-F=npy", "-o=output", "-i",
                       answers=b"no\nyes\n")
        numpy.testing.assert_array_equal(numpy.load("output/stack_0000.npy"), [42])
        numpy.testing.assert_array_equal(numpy.load("output/stack_0001.npy"), arrays[1])
        now = time.time()
        os.utime("input/stack.edf", (now - 10, now - 10))
        os.utime("output/stack_0000.npy", (now - 20, now - 20))
        numpy.save("output/stack_0001.npy", numpy.array([43]))
        self.run_split("input/stack.edf", "-F=npy", "-o=output", "-u")
        numpy.testing.assert_array_equal(numpy.load("output/stack_0000.npy"), arrays[0])
        numpy.testing.assert_array_equal(numpy.load("output/stack_0001.npy"), [43])

    def test_split_449_single_frame_and_batch(self):
        self.run_split("input/0*.edf", "-F=npy", "-o=output")
        for i in range(1, 4):
            with fabio.open(f"input/{i:02d}.edf") as source:
                numpy.testing.assert_array_equal(
                    numpy.load(f"output/{i:02d}_0000.npy"), source.data
                )

    def test_split_449_rejects_ambiguous_output(self):
        err = self.run_split("input/0*.edf", "-o=output/custom.npy", expected=2)
        self.assertIn(b"output directory", err)
        self.assertFalse(os.path.exists("output/custom_0000.npy"))

    def test_split_449_protects_input(self):
        self.create_stack("input/stack_0000.edf")
        with open("input/stack_0000.edf", "rb") as stream:
            original = stream.read()
        self.run_split("input/stack_0000.edf", "-o=input/stack.edf", "-f", expected=1)
        with open("input/stack_0000.edf", "rb") as stream:
            self.assertEqual(stream.read(), original)
        self.assertFalse(os.path.exists("input/stack_0001.edf"))

    def test_split_449_failure_does_not_skip_next_input(self):
        with open("input/00.edf", "wb") as stream:
            stream.write(b"corrupt image")
        self.run_split("input/00.edf", "input/03.edf", "-F=npy", "-o=output", expected=1)
        self.assertTrue(os.path.exists("output/03_0000.npy"))

    def test_split_449_rejects_duplicate_destinations(self):
        for directory in ("input/a", "input/b"):
            os.mkdir(directory)
            self.create_stack(directory + "/stack.edf")
        self.run_split("input/a/stack.edf", "input/b/stack.edf", "-F=npy",
                       "-o=output", "-f", expected=1)
        numpy.testing.assert_array_equal(numpy.load("output/stack_0000.npy"),
                                         numpy.arange(12).reshape(3, 4))

    def test_split_449_output_failure(self):
        self.create_stack()
        self.run_split("input/stack.edf", "-o=missing/stack.npy", expected=1)

    def test_split_449_preserves_format_conversion(self):
        values = numpy.array([[1.25, -2.75], [3.5, 4.0]])
        image = fabio.edfimage.EdfImage(data=values)
        image.append_frame(data=values + 10)
        image.write("input/float.edf")
        self.run_split("input/float.edf", "-F=cbf", "-o=output")
        for i in range(2):
            with fabio.open(f"output/float_{i:04d}.cbf") as result:
                numpy.testing.assert_array_equal(result.data, (values + 10 * i).astype(int))

    def test_split_449_protects_input_alias(self):
        self.create_stack()
        os.link("input/stack.edf", "output/stack_0000.edf")
        with open("input/stack.edf", "rb") as stream:
            original = stream.read()
        self.run_split("input/stack.edf", "-F=edf", "-o=output", "-f", expected=1)
        with open("output/stack_0000.edf", "rb") as stream:
            self.assertEqual(stream.read(), original)
        self.assertFalse(os.path.exists("output/stack_0001.edf"))

    def test_split_449_protects_other_input(self):
        self.create_stack()
        self.create_stack("output/stack_0001.edf")
        with open("output/stack_0001.edf", "rb") as stream:
            original = stream.read()
        self.run_split("input/stack.edf", "output/stack_0001.edf", "-F=edf",
                       "-o=output", "-f", expected=1)
        with open("output/stack_0001.edf", "rb") as stream:
            self.assertEqual(stream.read(), original)
        self.assertFalse(os.path.exists("output/stack_0000.edf"))

    def test_split_449_failed_frame_does_not_skip_later_frames(self):
        arrays = self.create_stack()
        os.mkdir("output/stack_0000.npy")
        self.run_split("input/stack.edf", "-F=npy", "-o=output", "-f", expected=1)
        self.assertTrue(os.path.isdir("output/stack_0000.npy"))
        numpy.testing.assert_array_equal(numpy.load("output/stack_0002.npy"), arrays[2])


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestFabioConvert))
    return testsuite


if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite())
