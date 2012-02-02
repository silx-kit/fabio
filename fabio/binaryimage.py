#!/usr/bin/env python
#coding: utf8 

"""
Authors: Gael Goret, Jerome Kieffer, ESRF, France
Emails: gael.goret@esrf.fr, jerome.kieffer@esrf.fr

Binary files images are simple none-compressed 2D images only defined by their : 
data-type, dimensions, byte order and offset

This simple library has been made for manipulating exotic/unknown files format.  
"""

__author__ = "Gaël Goret, Jérôme Kieffer"
__contact__ = "gael.goret@esrf.fr, jerome.kieffer@esrf.eu"
__license__ = "GPLv3+"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__version__ = "02 feb 2012"

from fabioimage import fabioimage
import numpy, struct, string, time, sys, logging
logger = logging.getLogger("binaryimage")

class binaryimage(fabioimage):
    def __init__(self, *args, **kwargs):
        fabioimage.__init__(self, *args, **kwargs)

    def swap_needed(self,endian):
        """
        Decide if we need to byteswap
        """
        if (endian =='<' and numpy.little_endian) or (endian == '>' and not numpy.little_endian):
            return False
        if (endian == '>' and numpy.little_endian) or (endian == '<' and not numpy.little_endian):
            return True

    def read(self, fname, dim1,dim2,offset=0,bytecode="int32",endian="<"):
        """ 
        Read a binary image
        Parameters : fname, dim1, dim2, offset, bytecode, endian
        fname : file name : str
        dim1,dim2 : image dimensions : int
        offset : size of the : int 
        bytecode among : "int8","int16","int32","int64","uint8","uint16","uint32","uint64","float32","float64",...
        endian among short or long endian ("<" or ">")
        """
        self.filename = fname
        self.dim1 = dim1
        self.dim2 = dim2
        self.bytecode = bytecode
        f = open(self.filename, "rb")
        dims = [dim2,dim1]
        bpp = len(numpy.array(0, bytecode).tostring())
        size = dims[0]*dims[1]*bpp
        
        f.seek(offset)
        rawData = f.read(size)
        if  self.swap_needed(endian):
            data = numpy.fromstring(rawData, bytecode).byteswap().reshape(tuple(dims))
        else:
            data = numpy.fromstring(rawData, bytecode).reshape(tuple(dims))
        self.data = data
        return self

    def estimate_offset_value(self,fname, dim1, dim2, bytecode="int32"):
        f = open(fname, "rb")
        bpp = len(numpy.array(0, bytecode).tostring())
        size = dim1*dim2*bpp
        totsize = len(f.read())
        print 'total size (bytes): ',totsize
        print 'expected data size given parameters (bytes) : ', size
        print 'estimation of the offset value (bytes): ',totsize - size

    def write(self, fname):
        outfile = open(fname, mode="wb")
        outfile.write(self.data.tostring())
        outfile.close()
            
            
