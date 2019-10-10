#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

import numpy
import os.path
import shutil
import sys
import subprocess
import time
import unittest
import logging

_logger = logging.getLogger(__name__)

import fabio.app.convert
from .utilstest import UtilsTest


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
        env = dict((str(k), str(v)) for k, v in os.environ.items())
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
        p = subprocess.Popen(commandLine, env=self.__env, shell=False,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
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
        assert(os.path.exists("output/03.msk"))
        image = fabio.open("output/03.msk")
        assert(isinstance(image, fabio.fit2dmaskimage.Fit2dMaskImage))
        assert(image.data.shape == (100, 100))

    def testSingleFileToDir(self):
        p = self.subprocessFabioConvert("input/03.edf", "-F=msk", "-o=output")
        self.logCommunicate(p)
        assert(os.path.exists("output/03.msk"))

    def testSingleFileWithWildcardToDir(self):
        p = self.subprocessFabioConvert("input/03.*", "-F=msk", "-o=output")
        self.logCommunicate(p)
        assert(os.path.exists("output/03.msk"))

    def testFullFormatName(self):
        p = self.subprocessFabioConvert("input/03.*", "-F=numpyimage", "-o=output")
        self.logCommunicate(p)
        assert(os.path.exists("output/03.npy"))
        image = fabio.open("output/03.npy")
        assert(isinstance(image, fabio.numpyimage.NumpyImage))
        assert(image.data.shape == (100, 100))

    def testForceOption(self):
        date1 = os.path.getmtime("output/01.msk")
        date2 = os.path.getmtime("output/02.msk")
        p = self.subprocessFabioConvert("input/*.edf", "-f", "-F=msk", "-o=output")
        self.logCommunicate(p)
        assert(os.path.exists("output/01.msk"))
        assert(date1 < os.path.getmtime("output/01.msk"))
        assert(os.path.exists("output/02.msk"))
        assert(date2 < os.path.getmtime("output/02.msk"))
        assert(os.path.exists("output/03.msk"))

    def testRemoveDestinationOption(self):
        date1 = os.path.getmtime("output/01.msk")
        date2 = os.path.getmtime("output/02.msk")
        p = self.subprocessFabioConvert("input/*.edf", "--remove-destination", "-F=msk", "-o=output")
        self.logCommunicate(p)
        assert(os.path.exists("output/01.msk"))
        assert(date1 < os.path.getmtime("output/01.msk"))
        assert(os.path.exists("output/02.msk"))
        assert(date2 < os.path.getmtime("output/02.msk"))
        assert(os.path.exists("output/03.msk"))

    def testNoClobberOption(self):
        date1 = os.path.getmtime("output/01.msk")
        date2 = os.path.getmtime("output/02.msk")
        p = self.subprocessFabioConvert("input/*.edf", "-n", "-F=msk", "-o=output")
        self.logCommunicate(p)
        assert(os.path.exists("output/01.msk"))
        assert(date1 == os.path.getmtime("output/01.msk"))
        assert(os.path.exists("output/02.msk"))
        assert(date2 == os.path.getmtime("output/02.msk"))
        assert(os.path.exists("output/03.msk"))

    def testUpdateOption(self):
        date1 = os.path.getmtime("output/01.msk")
        date2 = os.path.getmtime("output/02.msk")
        p = self.subprocessFabioConvert("input/*.edf", "--update", "-F=msk", "-o=output")
        self.logCommunicate(p)
        assert(os.path.exists("output/01.msk"))
        assert(date1 < os.path.getmtime("output/01.msk"))
        assert(os.path.exists("output/02.msk"))
        assert(date2 == os.path.getmtime("output/02.msk"))
        assert(os.path.exists("output/03.msk"))

    def testDefaultOption(self):
        date1 = os.path.getmtime("output/01.msk")
        date2 = os.path.getmtime("output/02.msk")
        p = self.subprocessFabioConvert("input/*.edf", "-F=msk", "-o=output")
        p.stdin.write(b'yes\n')
        p.stdin.write(b'no\n')
        self.logCommunicate(p)
        assert(os.path.exists("output/01.msk"))
        assert(date1 < os.path.getmtime("output/01.msk"))
        assert(os.path.exists("output/02.msk"))
        assert(date2 == os.path.getmtime("output/02.msk"))
        assert(os.path.exists("output/03.msk"))

    def testInteractiveOption(self):
        date1 = os.path.getmtime("output/01.msk")
        date2 = os.path.getmtime("output/02.msk")
        p = self.subprocessFabioConvert("input/*.edf", "-n", "-i", "-F=msk", "-o=output")
        p.stdin.write(b'yes\n')
        p.stdin.write(b'no\n')
        self.logCommunicate(p)
        assert(os.path.exists("output/01.msk"))
        assert(date1 < os.path.getmtime("output/01.msk"))
        assert(os.path.exists("output/02.msk"))
        assert(date2 == os.path.getmtime("output/02.msk"))
        assert(os.path.exists("output/03.msk"))


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestFabioConvert))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
