# coding: utf-8
# /*##########################################################################
#
# Copyright (c) 2015-2016 European Synchrotron Radiation Facility
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
# ###########################################################################*/
"""Wrapper module for the `gzip` library.

Feed this module using a local copy of `gzip` if it exists.
Else it expect to have an available `gzip` library installed in
the Python path.

It should be used like that:

.. code-block::

    from fabio.third_party import gzip

"""

from __future__ import absolute_import

__authors__ = ["Valentin Valls"]
__license__ = "MIT"
__date__ = "28/07/2017"

import sys as __sys

if __sys.version_info < (2, 7):
    # Try to import our local version of six
    from ._local.gzip import *  # noqa
else:
    # Else try to import it from the python path

    # Importing star here is not working
    # from gzip import *  # noqa

    import gzip as __gzip
    for k, v in __gzip.__dict__.items():
        if k.startswith("_"):
            continue
        vars()[k] = v
