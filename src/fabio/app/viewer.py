#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Project: Fast Azimuthal integration
#             https://github.com/silx-kit/pyFAI
#
#
#    Copyright (C) European Synchrotron Radiation Facility, Grenoble, France
#
#    Authors: Gael Goret <gael.goret@esrf.fr>
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
Portable diffraction images viewer/converter

* Written in Python, it combines the functionalities of the I/O library fabIO
  with a user friendly Qt GUI.
* Image converter is also a light viewer based on the visualization tool
  provided by the module matplotlib.
"""

__version__ = "1.1"
__author__ = "Gaël Goret, Jérôme Kieffer"
__copyright__ = "2015-2026 ESRF"
__licence__ = "MIT"
__date__ = "12/03/2026"


import sys
from argparse import ArgumentParser
import numpy
import fabio

# ----------------------------------------------------------------------
# Qt imports via QtPy – this works with PyQt5, PySide2, PySide6, etc.
# ----------------------------------------------------------------------
from qtpy.QtWidgets import QApplication, QStyleFactory
from ..qt.viewer import AppForm

# Matplotlib imports (unchanged)
# ----------------------------------------------------------------------
# Global configuration
# ----------------------------------------------------------------------
numpy.seterr(divide="ignore")

output_format = [
    "*.bin",
    "*.cbf",
    "*.edf",
    "*.h5",
    "*.img",
    "*.mar2300",
    "*.mar3450",
    "*.marccd",
    "*.tiff",
    "*.sfrm",
]


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
def main():
    parser = ArgumentParser(
        prog="fabio_viewer",
        usage="fabio_viewer img1 img2... imgn",
        description=__doc__,
        epilog=f"Based on FabIO version {fabio.version}",
    )
    parser.add_argument("images", nargs="*")
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=__version__,
        help="Print version & quit",
    )
    args = parser.parse_args()
    QApplication.setStyle(QStyleFactory.create("Cleanlooks"))
    app = QApplication([])
    form = AppForm()
    if args.images:
        form.open_data_series(args.images)
    form.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
