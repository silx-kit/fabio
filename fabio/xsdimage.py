#!/usr/bin/env python
# coding: utf8
"""
Authors: Jérôme Kieffer, ESRF 
         email:jerome.kieffer@esrf.fr

XSDimge are XML files containing numpy arrays 
"""
__author__ = "Jérôme Kieffer"
__contact__ = "jerome.kieffer@esrf.eu"
__license__ = "GPLv3+"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"

import os, logging, struct
import numpy as np
from fabio.fabioimage import fabioimage

from lxml import etree

class xsdimage(fabioimage):
    """ 
    Read the XSDataImage XML File data format 
    """
    def __init__(self, data=None, header=None, fname=None):
        """
        Constructor of the class XSDataImage.

        @param _strFilename: the name of the file to open
        @type  _strFilename: string
        """
        fabioimage.__init__(self, data=data, header=header)
        if fname is not None:
            self.filename = fname

    def read(self, fname):
        """
        """
        self.header = {}
        self.resetvals()
        self.filename = fname
        infile = self._open(fname, "rb")
        self._readheader(infile)

    def _readheader(self, infile):
        """
        Read all headers in a file and populate self.header
        data is not yet populated
        @type infile: file object open in read mode
        """
        xml = etree.parse(infile)
        dims = []
        for i in xml.xpath("//shape"):
            try:
                dims.append(int(i.text))
            except ValueError:
                logging.warning("Unable to convert %s to integer in %s" % (i.text, i))
        self.rawData = xml.xpath("//data")



