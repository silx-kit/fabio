#!/usr/bin/env python
#coding: utf-8
#This is a template for adding new file formats to FabIO

# We hope it will be relatively easy to add new file formats to fabio in the future. The basic idea is the following:
# 1) inherit from fabioimage overriding the methods _readheader, read and optionally write.
#    Name your new module XXXimage where XXX means something (eg tifimage).
#
# 2) readheader fills in a dictionary of "name":"value" pairs in self.header.
#    No one expects to find anything much in there.
#
# 3) read fills in self.data with a numpy array holding the image.
#    Some redundant info which also appears are self.dim1 and self.dim2: the image dimensions,
#    self.bpp is the bytes per pixel and self.bytecode is the numpy.dtype.type of the data.
#
# 4) The member variables "_need_a_seek_to_read" and "_need_a_real_file" are there in case you have
#    trouble with the transparent handling of bz2 and gz files.
#
# 5) Register the file type (extension naming) in fabioutils.FILETYPES
#
# 6) Add your new module as an import into fabio.openimage
#
# 7) Fill out the magic numbers for your format in fabio.openimage if you know them
#    (the characteristic first few bytes in the file)
#
# 8) Upload a testimage to the file release system and create a unittest testcase
#    which opens an example of your new format, confirming the image has actually
#    been read in successfully (eg check the mean, max, min and esd are all correct,
#    perhaps orientation too)
#
# 9) Run pylint on your code and then please go clean it up. Have a go at mine while you are at it.
#
#10) Bask in the warm glow of appreciation when someone unexpectedly learns they don't need to convert
#    their data into another format

"""
Template for FabIO

Authors: Who are you ?
email:  Where can you be reached ?

"""
# Get ready for python3:
from __future__ import with_statement, print_function, division

__authors__ = ["author"]
__contact__ = "name@institut.org"
__license__ = "GPLv3+"
__copyright__ = "Institut"
__version__ = "17 Oct 2012"

import logging
logger = logging.getLogger("templateimage")
import numpy
from .fabioimage import fabioimage



class templateimage(fabioimage):
    """
    FabIO image class for Images for XXX detector
    """
    def __init__(self, *arg, **kwargs):
        """
        Generic constructor
        """
        fabioimage.__init__(self, *arg, **kwargs)
        self.data = None
        self.header = {}
        self.dim1 = self.dim2 = 0
        self.m = self.maxval = self.stddev = self.minval = None
        self.header_keys = self.header.keys()
        self.bytecode = None

    def _readheader(self, infile):
        """
        Read and decode the header of an image:
        
        @param infile: Opened python file (can be stringIO or bipped file)  
        """
        #list of header key to keep the order (when writing)
        self.header = {}
        self.header_keys = []


    def read(self, fname, frame=None):
        """
        try to read image 
        @param fname: name of the file
        @param frame: 
        """

        self.resetvals()
        infile = self._open(fname)
        self._readheader(infile)

        #read the image data
        self.data = numpy.zeros((self.dim2, self.dim1), dtype=self.bytecode)
        return self
