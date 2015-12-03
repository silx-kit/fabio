# coding: utf-8
#
#    Project: X-ray image reader
#             https://github.com/kif/fabio
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
Authors: Jérôme Kieffer, ESRF
         email:jerome.kieffer@esrf.fr

XSDimge are XML files containing numpy arrays
"""
# Get ready for python3:
from __future__ import absolute_import, print_function, with_statement, division
__author__ = "Jérôme Kieffer"
__contact__ = "jerome.kieffer@esrf.eu"
__license__ = "GPLv3+"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"

import logging, numpy
logger = logging.getLogger("xsdimage")
from .fabioimage import FabioImage
from .fabioutils import six

import base64, hashlib
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
            assert  hashlib.md5(decData).hexdigest() == self.md5


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


