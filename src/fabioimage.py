#!/usr/bin/env python 
"""

Authors: Henning O. Sorensen & Erik Knudsen
         Center for Fundamental Research: Metal Structures in Four Dimensions
         Risoe National Laboratory
         Frederiksborgvej 399
         DK-4000 Roskilde
         email:erik.knudsen@risoe.dk
         
         and Jon Wright, ESRF

"""

import Numeric
from PIL import Image


#
# utilities to convert between numerical arrays and PIL image memories
#
# fredrik lundh, october 1998
#
# fredrik@pythonware.com
# http://www.pythonware.com
#
# http://effbot.org/zone/pil-numpy.htm   viewed on 20-8-2007

def image2array(im):
    if im.mode not in ("L", "F"):
        raise ValueError, "can only convert single-layer images"
    if im.mode == "L":
        a = Numeric.fromstring(im.tostring(), Numeric.UnsignedInt8)
    else:
        a = Numeric.fromstring(im.tostring(), Numeric.Float32)
    a.shape = im.size[1], im.size[0]
    return a

def array2image(a):
    if a.typecode() == Numeric.UnsignedInt8:
        mode = "L"
    elif a.typecode() == Numeric.Float32:
        mode = "F"
    else:
        raise ValueError, "unsupported image mode"
    return Image.fromstring(mode, (a.shape[1], a.shape[0]), a.tostring())






class fabioimage:
    """
    A common object for images in fable
    Contains a Numeric array (.data) and dict of meta data (.header)
    """
    def __init__(self, data = None , header = {}):
        """
        Set up initial values
        """
        if type(data) == type("string"):
            raise Exception("fabioimage.__init__ bad argument - "+\
                            "data should be Numeric array")
        self.data = data
        self.header = header
        self.header_keys = self.header.keys() # holds key ordering
        if data is not None:
            self.dim1, self.dim2 = data.shape
        else:
            self.dim1 = self.dim2 = 0
        self.bytecode = None     # Numeric typecode
        self.bpp = 2             # bytes per pixel
        # cache for image statistics
        self.m = self.maxval = self.stddev = self.minval = None
        # Cache roi
        self.area_sum = None
        self.slice = None

  
    def toPIL16(self, filename = None):
        """
        Convert to Python Imaging Library 16 bit greyscale image
        """
        if filename:
            self.read(filename)
        # >>> help(Image.frombuffer)
        # frombuffer(mode, size, data, decoder_name='raw', *args)
        # Load image from string or buffer
        # *args == raw mode, stride, orientation
        # raw mode 
        # The pixel layout used in the file, and is used to properly
        # convert data to PIL's internal layout. For a summary of the
        # available formats, see the table below.
        #
        # stride 
        #  The distance in bytes between two consecutive lines in the
        # image. If 0, the image is assumed to be packed (no padding
        # between lines). If omitted, the stride defaults to 0.
        #
        # orientation 
        # Whether the first line in the image is the top line on the
        # screen (1), or the bottom line (-1). If omitted, the orientation
        # defaults to 1.
        #
        #  mode  description
        #  "1"   1-bit bilevel, stored with the leftmost pixel in the
        #        most significant bit. 0 means black, 1 means white.
        #  "1;I" 1-bit inverted bilevel, stored with the leftmost pixel
        #        in the most significant bit. 0 means white, 1 means black.
        #  "1;R" 1-bit reversed bilevel, stored with the leftmost pixel
        #        in the least significant bit. 0 means black, 1 means white.
        #  "L"   8-bit greyscale. 0 means black, 255 means white.
        #  "L;I" 8-bit inverted greyscale. 0 means white, 255 means black.
        #  "P"   8-bit palette-mapped image.
        # "RGB"  24-bit true colour, stored as (red, green, blue).
        # "BGR"  24-bit true colour, stored as (blue, green, red).
        # "RGBX" 24-bit true colour, stored as (blue, green, red, pad).
        # "RGB;L" 24-bit true colour, line interleaved (first all red pixels,
        #         the all green pixels, finally all blue 
        bm = { Numeric.UInt8   : ["F", "F;8"]    ,  
               #  8-bit unsigned integer.
               Numeric.Int8    : ["F", "F;8S"]   ,  
               #  8-bit signed integer.
               Numeric.UInt16  : ["F", "F;16"]  ,  
               #  16-bit native unsigned integer.
               Numeric.Int16   : ["F", "F;16S"] ,  
               #  16-bit native signed integer.
               Numeric.UInt32  : ["F", "F;32N"]  ,  
               #  32-bit native unsigned integer.
               Numeric.Int32   : ["F", "F;32NS"] ,  
               #  32-bit native signed integer.
               Numeric.Float32 : ["F", "F;32NF"] }    
               #  32-bit native floating point.
        # Apparently does not work...:
             #  Numeric.Float64 : ["F","F;64NF"] }  
             #  64-bit native floating point
        #names = { Numeric.UInt8 : "Numeric.UInt8",
        #          Numeric.Int8  : "Numeric.Int8" ,  
        #          Numeric.UInt16: "Numeric.UInt16",  
        #          Numeric.Int16 :  "Numeric.Int16" ,  
        #          Numeric.UInt32:  "Numeric.UInt32" , 
        #          Numeric.Int32 :  "Numeric.Int32"   ,
        #          Numeric.Float32: "Numeric.Float32" ,
        #          Numeric.Float64:"Numeric.Float64"}
        try:
            byteformat = bm [ self.data.typecode() ]
            # print "Numeric typecode",self.data.typecode(),\
            #      "name",names[self.data.typecode()],byteformat
        except:
            raise Exception("Unknown data format in array!!!")
        try:
            PILimage = Image.frombuffer(byteformat[0],
                                        (self.data.shape[1],
                                         self.data.shape[0]),
                                        self.data,
                                        "raw", 
                                        byteformat[1], 
                                        0,  # whats this 
                                        1   # and this?  
                                        )
        except:
            print byteformat
            raise 
        return PILimage
        

    def getheader(self):
        """ returns self.header """
        return self.header
  
    def getmax(self):
        """ Find max value in self.data, caching for the future """
        if self.maxval is None:
            self.maxval = Numeric.maximum.reduce(
                                  Numeric.ravel(self.data))
        # FIXME - removed int cast to leave type alone
        return self.maxval
  
    def getmin(self):    
        """ Find min value in self.data, caching for the future """
        if self.minval is None:
            self.minval = Numeric.minimum.reduce(
                                  Numeric.ravel(self.data))
        # FIXME - removed int cast to leave type alone
        return self.minval

    def make_slice(self, coords):
        """
        Convert a len(4) set of coords into a len(2) 
        tuple (pair) of slice objects
        the latter are immutable, meaning the roi can be cached
        """
        assert len(coords) == 4
        if len(coords) == 4:
            # fabian edfimage preference
            if coords[0] > coords[2]:
                coords[0:3:2] = [coords[2], coords[0]]
            if coords[1] > coords[3]:
                coords[1:4:2] = [coords[3], coords[1]]
            #in fabian: normally coordinates are given as (x,y) whereas 
            # a matrix is given as row,col 
            # also the (for whichever reason) the image is flipped upside 
            # down wrt to the matrix hence these tranformations
            fixme = (self.dim2 - coords[3] - 1,
                     coords[0] ,
                     self.dim2 - coords[1] - 1,
                     coords[2])
        return ( slice(int(fixme[0]), int(fixme[2])+1) , 
                 slice(int(fixme[1]), int(fixme[3])+1)  )
        

    def integrate_area(self, coords):
        """ 
        Sums up a region of interest 
        if len(coords) == 4 -> convert coords to slices
        if len(coords) == 2 -> use as slices
        floor -> ? removed as unused in the function.
        """
        if self.data == None:
            # This should return NAN, not zero ?
            return 0
        if len(coords) == 4:
            sli = self.make_slice(coords)
        elif len(coords) == 2 and isinstance(coords[0], slice) and \
                                  isinstance(coords[1], slice):
            sli = coords
        if sli == self.slice and self.area_sum is not None:
            return self.area_sum
        self.slice = sli
        self.area_sum = Numeric.sum( 
                            Numeric.ravel( 
                                self.data[ self.slice ].astype(Numeric.Float)))
        return self.area_sum

    def getmean(self):
        """ return the mean """
        if self.m is None:
            self.m = Numeric.sum( Numeric.ravel( self.data.astype(Numeric.Float)))
            # use data.shape in case dim1 or dim2 are wrong
            self.m = self.m / (self.data.shape[0]*self.data.shape[1])
        return float(self.m)
    
    def getstddev(self):
        """ return the standard deviation """
        if self.m == None:
            self.getmean()    
        if self.stddev == None:
            # use data.shape in case dim1 or dim2 are wrong
            # formula changed from that found in edfimage by JPW
            Npt = self.data.shape[0] * self.data.shape[1] - 1
            diff = self.data.astype(Numeric.Float) - self.m
            Sumsq = Numeric.sum( Numeric.ravel( diff*diff ) )
            self.stddev = Numeric.sqrt(Sumsq / Npt)
        return float(self.stddev)

    def add(self, other):
        """
        Add another Image - warnign, does not clip to 16 bit images by default
        """
        if not hasattr(other,'data'):
            print 'edfimage.add() called with something that does not have a data field'
        assert self.data.shape == other.data.shape , \
                  'incompatible images - Do they have the same size?'
        self.data = self.data + other.data
        self.resetvals()
            
      
    def resetvals(self):
        """ Reset cache - call on changing data """
        self.m = self.stddev = self.maxval = self.minval = None
        self.area_sum = None
  
    def rebin(self, x_rebin_fact, y_rebin_fact):
        """ Rebin the data and adjust dims """
        if self.data == None:
            raise Exception('Please read in the file you wish to rebin first')
        (mx, ex) = math.frexp(x_rebin_fact)
        (my, ey) = math.frexp(y_rebin_fact)
        if (mx != 0.5 or my != 0.5):
            raise Exception('Rebin factors not power of 2 not supported (yet)')
        if int(self.dim1 / x_rebin_fact) * x_rebin_fact != self.dim1 or \
           int(self.dim2 / x_rebin_fact) * x_rebin_fact != self.dim2 :
            raise('image size is not divisible by rebin factor - skipping rebin')
        self.data.savespace(1) # avoid the upcasting behaviour
        i = 1
        while i < x_rebin_fact:
            # FIXME - why do you divide by 2? Rebinning should increase counts?
            self.data = ((self.data[:, ::2] + self.data[:, 1::2])/2)
            i = i * 2
        i = 1
        while i < y_rebin_fact:
            self.data = ((self.data[::2, :]+self.data[1::2, :])/2)
            i = i * 2
        self.resetvals()
        self.dim1 = self.dim1 / x_rebin_fact
        self.dim2 = self.dim2 / y_rebin_fact
        #update header
        self.update_header()
        
    def write(self,fname):
        """
        To be overwritten - write the file
        """
        raise Exception("Class has not implemented readheader method yet")
        
    def readheader(self, file_obj):
        """
        To be overridden - fill in self.header 
        """
        raise Exception("Class has not implemented readheader method yet")

    def update_header(self , **kwds):
        """
        update the header entries
        by default pass in a dict of key, values.
        """
        self.header.update(kwds)


    def read(self, filename):
        """
        To be overridden - fill in self.header and self.data
        """
        raise Exception("Class has not implemented read method yet")

    def _open(self, fname, mode="rb"):
        """
        Try to handle compressed files, streams, shared memory etc
        Return an object which can be used for "read" and "write" 
        ... FIXME - what about seek ? 
        """
        if hasattr(fname, "read") and hasattr(fname, "write"):
            # It is already something we can use
            return fname
        if type(fname) in [type(" "), type(u" ")]:
            import os
            if os.path.splitext(fname)[1] == ".gz":
                import gzip
                return gzip.GzipFile(fname, mode)
            if os.path.splitext(fname)[1] == '.bz2':
                import bz2
                return bz2.BZ2File(fname, mode)
            return open(fname, mode)

if __name__=='__main__':
    import time
    start = time.time()
    
    d = Numeric.ones((1024,1024), Numeric.UInt16)
    d = (d*50000).astype(Numeric.UInt16)
    assert d.typecode() == Numeric.ones((1),Numeric.UInt16).typecode()
    h = {"Title":"50000 everywhere"}
    o = fabioImage(d,h)
      
    assert o.getmax() == 50000
    assert o.getmin() == 50000
    assert o.getmean() == 50000 , o.getmean()
    assert o.getstddev() == 0.
      
    d2 = Numeric.zeros((1024,1024), Numeric.UInt16, savespace = 1 )
    c = [ 256, 256, 790, 768 ]
    s = o.make_slice(c)
    d2[s] = d2[s] + 100
      
    o = fabioImage(d2, h)
      
    # New object, so...
    assert o.maxval is None
    assert o.minval is None
     
    assert o.getmax() == 100, o.getmax()
    assert o.getmin() == 0 , o.getmin()
    npix = (s[0].stop-s[0].start)*(s[1].stop-s[1].start)
    o.resetvals()
    a1 = o.integrate_area(c) 
    o.resetvals()
    a2 = o.integrate_area(s)
    assert o.integrate_area(c) == o.integrate_area(s)
    assert o.integrate_area(c) == npix*100, o.integrate_area(c)
    

    import os

    def clean():
        for name in ["testfile","testfile.gz", "testfile.bz2"]:
            try:
                os.remove(name)
            except:
                pass
        
    clean()
    
    open("testfile","wb").write("{ hello }")
    os.system("gzip testfile")
    fo = o._open("testfile.gz")
    r = fo.read()
    assert r == "{ hello }", r+" gzipped file"
    
    open("testfile","wb").write("{ hello }")  
    os.system("bzip2 testfile")
    fo = o._open("testfile.bz2")
    r = fo.read()
    assert r == "{ hello }", r+" bzipped file"
    
    ft = open("testfile","wb")
    ft.write("{ hello }")
    assert ft == o._open(ft)
    ft.close()
    fo = o._open("testfile")
    r = fo.read()
    assert r == "{ hello }", r+"plain file"
    fo.close()
    ft.close()
    clean()
    
    print "Passed in",time.time()-start,"s"
