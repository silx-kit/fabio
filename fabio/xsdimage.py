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

__author__ = "Jérôme Kieffer"
__contact__ = "jerome.kieffer@esrf.eu"
__license__ = "MIT"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"

import logging
import numpy
import base64
import hashlib

from .fabioimage import FabioImage

logger = logging.getLogger(__name__)

try:
    import lxml.etree as etree
except ImportError:
    try:
        # Try using the standard library
        import xml.etree.ElementTree as etree
    except ImportError:
        logger.warning("xml/lxml library is probably not part of your python installation: disabling xsdimage format")
        etree = None


class XsdImage(FabioImage):
    """
    Read the XSDataImage XML File data format
    """

    DESCRIPTION = "XSDataImage XML file format"

    DEFAULT_EXTENSIONS = ["xml", "xsd"]

    def __init__(self, data=None, header=None, fname=None):
        """
        Constructor of the class XSDataImage.

        :param str fname: the name of the file to open
        """
        FabioImage.__init__(self, data=data, header=header)
        self._shape = []
        self.size = None
        self.coding = None
        self._dtype = None
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

        with self._open(fname, "rb") as infile:
            self._readheader(infile)

        exp_size = 1
        for i in self.shape:
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

        data = numpy.frombuffer(decData, dtype=self._dtype)
        data.shape = self.shape
        self.data = data

        if not numpy.little_endian:  # by default little endian
            self.data.byteswap(inplace=True)
        self.resetvals()
        return self

    def _readheader(self, infile):
        """
        Read all headers in a file and populate self.header
        data is not yet populated
        :type infile: file object open in read mode
        """
        xml = etree.parse(infile)
        self._shape = []
        for i in xml.findall(".//shape"):
            try:
                self._shape.insert(0, int(i.text))
            except ValueError as error:
                logger.warning("%s Shape: Unable to convert %s to integer in %s" % (error, i.text, i))
        self._shape = tuple(self._shape)

        for i in xml.findall(".//size"):
            try:
                self.size = int(i.text)
            except Exception as error:
                logger.warning("%s Size: Unable to convert %s to integer in %s" % (error, i.text, i))

        self._dtype = None
        for i in xml.findall(".//dtype"):
            self._dtype = numpy.dtype(i.text)
        self.coding = None
        for i in xml.findall(".//coding"):
            j = i.find("value")
            if j is not None:
                self.coding = j.text
        self.rawData = None
        for i in xml.findall(".//data"):
            self.rawData = i.text.encode("latin-1")
        self.md5 = None
        for i in xml.findall(".//md5sum"):
            j = i.find("value")
            if j is not None:
                self.md5 = j.text


if etree is None:
    # Hide the class if it can't work
    XsdImage = None

xsdimage = XsdImage
