#!/usr/bin/python
# coding: utf-8
#
#    Copyright (C) European Synchrotron Radiation Facility, Grenoble, France
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

"""Benchmark for file reading"""

__author__ = "Jérôme Kieffer"
__date__ = "10/02/2023"
__license__ = "MIT"
__copyright__ = "2016-2020 European Synchrotron Radiation Facility, Grenoble, France"

import json
import sys
import time
import timeit
import os
import platform
import subprocess
import numpy
import fabio
import os.path as op
import logging

# To use use the locally build version of PyFAI, use ../bootstrap.py
try:
    from .. import open as fabio_open, version, date
except ImportError:
    from fabio import open as fabio_open, version, date
from ..test import utilstest

datasets = ["mb_LP_1_001.img",
            "Cr8F8140k103.0026",
            "run2_1_00148.cbf",
            "F2K_Seb_Lyso0675.edf",
            "fit2d_click.msk",
            "GE_aSI_detector_image_1529",
            "i01f0001.kcd",
            "example.mar2300",
            "corkcont2_H_0089.mccd",
            "b191_1_9_1.img",
            "image0001.pgm",
            "mgzn-20hpt.img",
            "oPPA_5grains_0001.tif",
            "XSDataImage.xml", ]

setup = """
import fabio
"""
stmt = "data = fabio.open(r'%s').data"


def run_benchmark(number=10, repeat=3):
    """
    :param number: Measure timimg over number of executions
    :param repeat: number of measurement, takes the best of them

    """
    print(f"Benchmarking during {number} seconds (best of {repeat} iterations).")
    print(f"Python {sys.version}")
    print(f"FabIO {version} ({date})")
    print("#" * 80)
    print("     Module           filename        \t file size \t image size \t read time (ms) \t ms/Mpix")
    for img in datasets:
        fn = utilstest.UtilsTest.getimage(img)
        fimg = fabio_open(fn)
        file_size = os.stat(fn).st_size / 1.0e6  # MB
        img_size = fimg.data.size / 1.0e6  # Mpix
        timer = timeit.Timer(stmt % fn, setup + (stmt % fn))
        tmin = min([i / (0.001 * number) for i in timer.repeat(repeat=repeat, number=number)])
        print("%13s %25s %.3f Mb \t %.3f Mpix \t  %.3f ms \t %.3f ms/Mpix" %
              (fimg.__class__.__name__, img, file_size, img_size, tmin, tmin / img_size))


run = run_benchmark
