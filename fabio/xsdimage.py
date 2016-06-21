# coding: utf-8
#
#    Project: FabIO X-ray image reader
#
#    Copyright (C) 2010-2016 European Synchrotron Radiation Facility
#                       Grenoble, France
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
Authors: Jérôme Kieffer, ESRF
         email:jerome.kieffer@esrf.fr

XSDimge are XML files containing numpy arrays
"""
# Get ready for python3:
from __future__ import absolute_import, print_function, with_statement, division
__author__ = "Jérôme Kieffer"
__contact__ = "jerome.kieffer@esrf.eu"
__license__ = "MIT"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"

import logging
import numpy
import base64
import hashlib

from .fabioimage import FabioImage
from .fabioutils import six

logger = logging.getLogger("xsdimage")
try:
    from lxml import etree
except ImportError:
    logger.warning("lxml library is probably not part of your python installation: disabling xsdimage format")
    etree = None


class XsdImage(FabioImage):
    """
    Read the XSDataImage XML File data format
    """
    def __init__(self, data=None, header=None, fname=None):
        """
        Constructor of the class XSDataImage.

        @param _strFilename: the name of the file to open
        @type  _strFilename: string
        """
        FabioImage.__init__(self, data=data, header=header)
        self.dims = []
        self.size = None
        self.coding = None
        self.dtype = None
        self.rawData = None
        self.md5 = None
        if fname is not None:
            self.filename = fname
            self.read(fname)

    def read(self, fname, frame=None):
        """
        """
        self.header = {}
        self.resetvals()
        self.filename = fname
        infile = self._open(fname, "rb")
        self._readheader(infile)

        try:
            self.dim1, self.dim2 = self.dims[:2]
        except:
            raise IOError("XSD file %s is corrupt, no dimensions in it" % fname)

        exp_size = 1
        for i in self.dims:
            exp_size *= i
        assert exp_size == self.size

        decData = None
        if self.coding == "base64":
            decData = base64.b64decode(self.rawData)
        elif self.coding == "base32":
            decData = base64.b32decode(self.rawData)
        elif self.coding == "base16":
            decData = base64.b16decode(self.rawData)
        else:
            logger.warning("Unable to recognize the encoding of the data !!! got %s, expected base64, base32 or base16, I assume it is base64 " % self.coding)
            decData = base64.b64decode(self.rawData)
        if self.md5:
            assert hashlib.md5(decData).hexdigest() == self.md5

        self.data = numpy.fromstring(decData, dtype=self.dtype).reshape(tuple(self.dims))
        if not numpy.little_endian:  # by default little endian
            self.data.byteswap(True)
        self.resetvals()
#        # ensure the PIL image is reset
        self.pilimage = None
        return self

    def _readheader(self, infile):
        """
        Read all headers in a file and populate self.header
        data is not yet populated
        @type infile: file object open in read mode
        """
        xml = etree.parse(infile)
        self.dims = []
        for i in xml.xpath("//shape"):
            try:
                self.dims.append(int(i.text))
            except ValueError as error:
                logger.warning("%s Shape: Unable to convert %s to integer in %s" % (error, i.text, i))
        for i in xml.xpath("//size"):
            try:
                self.size = int(i.text)
            except Exception as error:
                logger.warning("%s Size: Unable to convert %s to integer in %s" % (error, i.text, i))
        self.dtype = None
        for i in xml.xpath("//dtype"):
            self.dtype = i.text
        self.coding = None
        for i in xml.xpath("//coding"):
            j = i.find("value")
            if j is not None:
                self.coding = j.text
        self.rawData = None
        for i in xml.xpath("//data"):
            self.rawData = six.b(i.text)
        self.md5 = None
        for i in xml.xpath("//md5sum"):
            j = i.find("value")
            if j is not None:
                self.md5 = j.text

if etree is None:
    XsdImage = None

xsdimage = XsdImage
