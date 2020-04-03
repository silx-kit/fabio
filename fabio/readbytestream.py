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

"""Reads a bytestream

Authors: Jon Wright    Henning O. Sorensen & Erik Knudsen
         ESRF          Risoe National Laboratory
"""

import logging
import numpy
logger = logging.getLogger(__name__)

DATATYPES = {
    # type  sign bytes
    ("int", 'n', 1): numpy.uint8,
    ("int", 'n', 2): numpy.uint16,
    ("int", 'n', 4): numpy.uint32,
    ("int", 'y', 1): numpy.int8,
    ("int", 'y', 2): numpy.int16,
    ("int", 'y', 4): numpy.int32,
    ('float', 'y', 4): numpy.float32,  # does this occur in bruker?
    ('double', 'y', 4): numpy.float64
}


def readbytestream(fil,
                   offset,
                   x,
                   y,
                   nbytespp,
                   datatype='int',
                   signed='n',
                   swap='n',
                   typeout=numpy.uint16):
    """
    Reads in a bytestream from a file (which may be a string indicating
    a filename, or an already opened file (should be "rb"))
    offset is the position (in bytes) where the pixel data start
    nbytespp = number of bytes per pixel
    type can be int or float (4 bytes pp) or double (8 bytes pp)
    signed: normally signed data 'y', but 'n' to try to get back the
    right numbers when unsigned data are converted to signed
    (python once had no unsigned numeric types.)
    swap, normally do not bother, but 'y' to swap bytes
    typeout is the numpy type to output, normally uint16,
    but more if overflows occurred
    x and y are the pixel dimensions

    TODO : Read in regions of interest

    PLEASE LEAVE THE STRANGE INTERFACE ALONE -
    IT IS USEFUL FOR THE BRUKER FORMAT
    """
    tin = "dunno"
    length = nbytespp * x * y  # bytes per pixel times number of pixels
    if datatype in ['float', 'double']:
        signed = 'y'

    key = (datatype, signed, nbytespp)
    try:
        tin = DATATYPES[key]
    except KeyError:
        logger.warning("datatype, signed, nbytespp: %s", str(key))
        raise Exception("Unknown combination of types to readbytestream")

    # Did we get a string (filename) or a readable stream object?
    if hasattr(fil, "read") and hasattr(fil, "seek"):
        infile = fil
        opened = False
    else:
        infile = open(fil, 'rb')
        opened = True

    infile.seek(offset)

    data = numpy.frombuffer(infile.read(length), tin)
    arr = numpy.array(numpy.reshape(data, (x, y)), typeout)

    if swap == 'y':
        arr.byteswap(True)

    if opened:
        infile.close()

    return arr
