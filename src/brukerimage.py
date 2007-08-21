#!/usr/bin/env python 
"""

Authors: Henning O. Sorensen & Erik Knudsen
         Center for Fundamental Research: Metal Structures in Four Dimensions
         Risoe National Laboratory
         Frederiksborgvej 399
         DK-4000 Roskilde
         email:erik.knudsen@risoe.dk

Based on: openbruker,readbruker, readbrukerheader functions in the opendata
         module of ImageD11 written by Jon Wright, ESRF, Grenoble, France

"""

import Numeric
import math
from PIL import Image
import os

class brukerimage:
  data=None
  header={}
  dim1=dim2=0
  m=maxval=stddev=minval=None
  header_keys=[]
  bytecode=None
  
  def toPIL16(self,filename=None):
    if filename:
      self.read(filename)
      PILimage=Image.frombuffer("F",(self.dim1,self.dim2),self.data,"raw","F;16",0,-1)
      return PILimage
    else:
      PILimage= Image.frombuffer("F",(self.dim1,self.dim2),self.data,"raw","F;16",0,-1)
      return PILimage

  def _readheader(self,f):
    l=f.read(512)
    i = 80
    self.header = {}
    while i < 512:
      key,val=l[i-80:i].split(":",1)   # uses 80 char lines in key : value format
      key=key.strip()         # remove the whitespace (why?)
      val=val.strip()
      if self.header.has_key(key):             # append lines if key already there
	self.header[key]=self.header[key]+'\n'+val
      else:
	self.header[key]=val
      i=i+80                  # next 80 characters

    nhdrblks=int(self.header['HDRBLKS'])    # we must have read this in the first 512 bytes.
    # Now read in the rest of the header blocks, appending to what we have
    rest=f.read(512*(nhdrblks-1))
    l = l[i-80:512] + rest
    j=512*nhdrblks
    while i < j :
      # print i,"*",block[i-80:i].strip(),"*"
      if l[i-80:i].find(":") > 0:          # as for first 512 bytes of header
	key,val=l[i-80:i].split(":",1)
        key=key.strip()
        val=val.strip()
        if self.header.has_key(key):
	  self.header[key]=self.header[key]+'\n'+val
        else:
          self.header[key]=val
      i=i+80
    self.header['datastart']=f.tell()        # make a header item called "datastart"
	
  def read(self,fname,verbose=0):
    f=open(fname,"rb")
    
    try:
      self._readheader(f)
    except:
      raise
    rows   =int(self.header['NROWS'])
    cols   =int(self.header['NCOLS'])
    
    try:
      npixelb=int(self.header['NPIXELB'])   # you had to read the Bruker docs to know this!
    except:
      print "length",len(self.header['NPIXELB'])
      for c in self.header['NPIXELB']:
	print "char:",c,ord(c)
      raise
    # We are now at the start of the image - assuming readbrukerheader worked
    size=rows*cols*npixelb
    self.data=self.readbytestream(f,f.tell(),rows,cols,npixelb,datatype="int",signed='n',swap='n')
    no=int(self.header['NOVERFL'])        # now process the overflows
    print no
    if no>0:   # Read in the overflows
        # need at least Int32 sized data I guess - can reach 2^21
        self.data=self.data.astype(Numeric.UInt32)
        # 16 character overflows, 9 characters of intensity, 7 character position
        for i in range(no):
            ov=f.read(16)
            intensity=int(ov[0:9])
            position=int(ov[9:16])
            r=position%rows           # relies on python style modulo being always +
            c=position/rows           # relies on truncation down
            #print "Overflow ",r,c,intensity,position,self.data[r,c],self.data[c,r]
            self.data[c,r]=intensity
    f.close()
    
    #now read the data into the array
    (self.dim1,self.dim2)=(rows,cols)
    print self.dim1, self.dim2
    self.resetvals()
    return self

  def readbytestream(self,file,offset,x,y,nbytespp,datatype='int',signed='n',
		swap='n',typeout=Numeric.UInt16):
    """
    Reads in a bytestream from a file (which may be a string indicating
    a filename, or an already opened file (should be "rb"))
    offset is the position (in bytes) where the pixel data start
    nbytespp = number of bytes per pixel
    type can be int or float (4 bytes pp) or double (8 bytes pp)
    signed: normally signed data 'y', but 'n' to try to get back the right numbers
      when unsigned data are converted to signed (python has no unsigned numeric types.)
    swap, normally do not bother, but 'y' to swap bytes
    typeout is the Numeric type to output, normally UInt16, but more if overflows occurred
    x and y are the pixel dimensions

    TODO : Read in regions of interest

    PLEASE LEAVE THE STRANGE INTERFACE ALONE - IT IS USEFUL FOR THE BRUKER FORMAT
    """
    tin="dunno"
    print datatype
    len=nbytespp*x*y # bytes per pixel times number of pixels
    if datatype=='int' and signed=='n':
        if nbytespp==1 : tin=Numeric.UInt8
        if nbytespp==2 : tin=Numeric.UInt16
        if nbytespp==4 : tin=Numeric.UInt32
    if datatype=='int' and signed=='y':
        if nbytespp==1 : tin=Numeric.Int8
        if nbytespp==2 : tin=Numeric.Int16
        if nbytespp==4 : tin=Numeric.Int32
    if datatype=='float':
        tin=Numeric.Float32
    if datatype=='double' :
        tin=Numeric.Float64
    if tin=="dunno" :
        raise SyntaxError, "Did not understand what type to try to read"
    if type(tin) == type(file):  # Did we get a string or a file pointer?
        f=open(file,'rb')
        opened=1
    else:
        f=file
    f.seek(offset)
    if swap=='y':
        ar=Numeric.array(Numeric.reshape(
           Numeric.byteswapped(Numeric.fromstring(f.read(len),tin)),(x,y)),typeout)
    else:
        ar=Numeric.array(Numeric.reshape(
                               Numeric.fromstring(f.read(len),tin) ,(x,y)),typeout)
    return ar

  def getheader(self):
    if self.header=={}:
      print "No file loaded"
    return self.header
  
  def getmax(self):
    if self.maxval==None:
      max_xel=Numeric.argmax(Numeric.ravel(self.data))
      self.maxval=Numeric.ravel(self.data)[max_xel]
    return int(self.maxval)
  
  def getmin(self):
    if self.minval==None:
      min_xel=Numeric.argmin(Numeric.ravel(self.data))
      self.minval=Numeric.ravel(self.data)[min_xel]
    return int(self.minval)


  def integrate_area(self,coords,floor=0):
    if not self.data:
      return 0
    else:
      if coords[0]>coords[2]:
	coords[0:3:2]=[coords[2],coords[0]]
      if coords[1]>coords[3]:
	coords[1:4:2]=[coords[3],coords[1]]
      S=Numeric.sum(Numeric.ravel(self.data[int(coords[0]):int(coords[2])+1,int(coords[1]):int(coords[3])+1]))
      S=S-floor*(1+coords[2]-coords[0])*(1+coords[3]-coords[1])
    return S

  def getmean(self):
    if self.m==None:
      self.m=Numeric.sum(Numeric.ravel(self.data.astype(Numeric.Float)))/(self.dim1*self.dim2)
    return float(self.m)
    
  def getstddev(self):
    if self.m==None:
      self.getmean()
      print "recalc mean"
    if self.stddev==None:
      N=self.dim1*self.dim2-1
      S=Numeric.sum(Numeric.ravel((self.data.astype(Numeric.Float)-self.m)/N*(self.data.astype(Numeric.Float)-self.m)) )
      self.stddev=S/(self.dim1*self.dim2-1)
    return float(self.stddev)

  def getheader(self):
    return self.header

  def add(self, otherImage):
    if not hasattr(otherImage,'data'):
      print 'brukerimage.add() called with something that does not have a data field'
    try:
      self.data=Numeric.clip(self.data+otherImage.data,0,65535)
    except:
      message='incompatible images - Do they have the same size?'
      
  def resetvals(self):
    self.m=self.stddev=self.maxval=self.minval=None
  
  def rebin(self,x_rebin_fact,y_rebin_fact):
    #not in working order yet
    if self.data==None:
      print 'Please read the file you wish to rebin first'
      return
    (mx,ex)=math.frexp(x_rebin_fact)
    (my,ey)=math.frexp(y_rebin_fact)
    if (mx!=0.5 or my!=0.5):
      print 'Rebin factors not power of 2 not supported (yet)'
      return
    if int(self.dim1/x_rebin_fact)*x_rebin_fact!=self.dim1 or int(self.dim2/x_rebin_fact)*x_rebin_fact!=self.dim2:
      print 'image size is not divisible by rebin factor - skipping rebin'
      return
    self.data.savespace(1)#avoid the upcasting behaviour
    i=1
    while i<x_rebin_fact:
      self.data=((self.data[:,::2]+self.data[:,1::2])/2)
      i=i*2
    i=1
    while i<y_rebin_fact:
      self.data=((self.data[::2,:]+self.data[1::2,:])/2)
      i=i*2
    self.resetvals()
    self.dim1=self.dim1/x_rebin_fact
    self.dim2=self.dim2/y_rebin_fact
    #update header
    self.header['Dim_1']=self.dim1
    self.header['Dim_2']=self.dim2
    self.header['col_end']=self.dim1-1
    self.header['row_end']=self.dim2-1
  
  def write(self,fname):
    f=open(fname,"wb")
    f.write('{\n')
    i=4
    for k in self.header_keys:
      out = (("%s = %s;\n") % (k,self.header[k]))
      i = i + len(out)
      f.write(out)
    out = (4096-i)*' '
    f.write(out)
    f.write('}\n')
    if self.header["ByteOrder"]=="LowByteFirst":
      f.write(self.data.astype(Numeric.UInt16).tostring())
    else:
      f.write(self.data.byteswapped().astype(Numeric.UInt16).tostring())
    f.close()

if __name__=='__main__':
  import sys,os,time
  I=brukerimage()
  b=time.clock()
  while (sys.argv[1:]):
    I.read(sys.argv[1])
    r=I.toPIL16()
    I.rebin(2,2)
    print sys.argv[1] + (": max=%d, min=%d, mean=%.2e, stddev=%.2e") % (I.getmax(),I.getmin(), I.getmean(), I.getstddev()) 
    print 'integrated intensity (%d %d %d %d) =%.3f' % (10,20,20,40,I.integrate_area((10,20,20,40)))
    sys.argv[1:]=sys.argv[2:]
  e=time.clock()
  print (e-b)
