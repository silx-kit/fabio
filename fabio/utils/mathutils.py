# coding: utf-8
#
#    Project: X-ray image reader
#             https://github.com/silx-kit/fabio
#
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
# THE SOFTWARE

"""Math function which can be useful on the full project
"""

import numpy


def naive_rad2deg(x):
    """
    Naive implementation of radiuan to degree.

    Useful for very old numpy (v1.0.1 on MacOSX from Risoe)
    """
    return 180.0 * x / numpy.pi


def naive_deg2rad(x):
    """
    Naive implementation of degree to radiuan.

    Useful for very old numpy (v1.0.1 on MacOSX from Risoe)
    """
    return x * numpy.pi / 180.


try:
    from numpy import rad2deg, deg2rad
except ImportError:
    # naive implementation for very old numpy (v1.0.1 on MacOSX from Risoe)
    rad2deg = naive_deg2rad
    deg2rad = naive_deg2rad
