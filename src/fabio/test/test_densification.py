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
#  Permission is hereby granted, free of charge, to any person
#  obtaining a copy of this software and associated documentation files
#  (the "Software"), to deal in the Software without restriction,
#  including without limitation the rights to use, copy, modify, merge,
#  publish, distribute, sublicense, and/or sell copies of the Software,
#  and to permit persons to whom the Software is furnished to do so,
#  subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be
#  included in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
#  OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#  NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#  HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
#  WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#  OTHER DEALINGS IN THE SOFTWARE.

__authors__ = ["Jérôme Kieffer"]
__contact__ = "Jerome.Kieffer@esrf.fr"
__license__ = "MIT"
__copyright__ = "2020 ESRF"
__date__ = "02/06/2022"

import unittest
import numpy
import logging
logger = logging.getLogger(__name__)
from ..sparseimage import densify, cython_densify
from ..ext.dense import distribution_uniform_mtc, distribution_normal_mtc


class TestDensification(unittest.TestCase):

    def test_rng_uniform(self):
        shape = (100, 100)
        U = distribution_uniform_mtc(shape).ravel()
        d, p = numpy.histogram(U, 100)
        eps = 1e-3
        self.assertGreater(p[0], 0)
        self.assertLess(p[0], eps)
        self.assertGreater(p[-1], 1 - eps)
        self.assertLess(p[-1], 1)
        self.assertGreater(d.min(), 50)
        self.assertLess(d.max(), 150)

    def test_rng_normal(self):
        shape = (100, 100)
        mu = 5.5
        sigma = 1.5
        one = numpy.ones(shape)
        N = distribution_normal_mtc(one * mu, one * sigma)
        self.assertAlmostEqual(N.mean(), mu, 1)
        self.assertAlmostEqual(N.std(), sigma, 1)

    def test_cython(self):
        seed = 0 
        shape = 256, 256
        nframes = 8
        vsize = 181  # This is cheated to avoid interpolation issues with rounding 128*sqrt(2)
        y, x = numpy.ogrid[-shape[0] // 2:-shape[0] // 2 + shape[0],
                          -shape[1] // 2:-shape[1] // 2 + shape[1]]
        # To make this test "robust", those two radial position arrays needs to be in float64 ... in production float32 is more common 
        r2d = numpy.sqrt(x * x + y * y).astype(numpy.float64)
        radius = numpy.linspace(0, r2d.max(), vsize).astype(numpy.float64)
        npeak = numpy.random.randint(90, 110, size=nframes)
        scale = numpy.random.randint(90, 110, size=nframes)
        osc = numpy.random.randint(40, 100, size=nframes)
        indptr = numpy.zeros(nframes + 1, dtype=int)
        indptr[1:] = numpy.cumsum(npeak)
        index = numpy.random.randint(0, numpy.prod(shape), size=npeak.sum()).astype(numpy.uint32)
        intensity = numpy.random.randint(0, 10, size=npeak.sum()).astype(numpy.uint16)
        frames = numpy.empty((nframes, *shape), dtype=numpy.uint16)
        background = numpy.empty((nframes, vsize), dtype=numpy.float32)
        noise = numpy.empty((nframes, vsize), dtype=numpy.float32)
        python = []
        cython = []
        for i, f in enumerate(frames):
            background[i] = numpy.arcsinh(scale[i] * numpy.sinc(radius / osc[i]) ** 2)
            noise[i] = abs(numpy.diff(background[i], prepend=background[i, 0]))
            f[...] = numpy.arcsinh(scale[i] * numpy.sinc(r2d / osc[i]) ** 2).round()
            f.ravel()[index[indptr[i]:indptr[i + 1]]] = intensity[indptr[i]:indptr[i + 1]]
            python = densify(r2d, radius, index[indptr[i]:indptr[i + 1]], intensity[indptr[i]:indptr[i + 1]], 0, background[i])
            cython = cython_densify.densify(r2d, radius, index[indptr[i]:indptr[i + 1]], intensity[indptr[i]:indptr[i + 1]], 0, intensity.dtype, background[i], None)
            
            self.assertTrue(numpy.all(python == cython), "python == cython #" + str(i))
            # Rounding errors:
            delta = (python.astype(int) - f)
            self.assertLessEqual(abs(delta).max(), 1, "Maximum difference is 1 due to rounding errors")
            bad = numpy.where(delta)
            print("#####", i)
            self.assertLess(len(bad[0]), numpy.prod(shape) / 500, "python differs from reference on less then 0.2% of the pixel #" + str(i))

            # Now consider the noise ...
            python = densify(r2d, radius, index[indptr[i]:indptr[i + 1]], intensity[indptr[i]:indptr[i + 1]], 0, background[i], noise[i], seed=seed)
            cython = cython_densify.densify(r2d, radius, index[indptr[i]:indptr[i + 1]], intensity[indptr[i]:indptr[i + 1]], 0, intensity.dtype, background[i], noise[i], seed=seed)
            self.assertTrue(abs(python.astype(int) - cython).max() <= 2 * max(1, noise[i].max()), "python is close to cython #" + str(i))


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestDensification))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
