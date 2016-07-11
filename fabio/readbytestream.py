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
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#


"""
Reads a bytestream

Authors: Jon Wright    Henning O. Sorensen & Erik Knudsen
         ESRF          Risoe National Laboratory
"""
# Get ready for python3:
from __future__ import with_statement, print_function, division

import numpy, logging
logger = logging.getLogger("readbytestream")
DATATYPES = {
    # type  sign bytes
    ("int", 'n', 1) : numpy.uint8,
    ("int", 'n', 2) : numpy.uint16,
    ("int", 'n', 4) : numpy.uint32,
    ("int", 'y', 1) : numpy.int8,
    ("int", 'y', 2) : numpy.int16,
    ("int", 'y', 4) : numpy.int32,
    ('float', 'y', 4) : numpy.float32,  # does this occur in bruker?
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
    except:
        logging.warning("datatype,signed,nbytespp " + str(key))
        raise Exception("Unknown combination of types to readbytestream")

    # Did we get a string (filename) or a readable stream object?
    if hasattr(fil, "read") and hasattr(fil, "seek"):
        infile = fil
        opened = False
    else:
        infile = open(fil, 'rb')
        opened = True

    infile.seek(offset)

    arr = numpy.array(numpy.reshape(
            numpy.fromstring(
                infile.read(length), tin) , (x, y)), typeout)

    if swap == 'y':
        arr = arr.byteswap()

    if opened:
        infile.close()

    return arr
