#!/usr/bin/env python 
"""

Authors: Henning O. Sorensen & Erik Knudsen
         Center for Fundamental Research: Metal Structures in Four Dimensions
         Risoe National Laboratory
         Frederiksborgvej 399
         DK-4000 Roskilde
         email:erik.knudsen@risoe.dk

"""

import Numeric
import math
from PIL import Image

class adscimage:
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
	
  def read(self,fname,verbose=0):
    f=open(fname,"rb")
    l=f.readline()
    bytesread = len(l)
    while '}' not in l:
      if '=' in l:
	(k,v)=l.split('=')
	self.header_keys.append(k.strip())
	self.header[k.strip()]=v.strip(' ;\n')
      l=f.readline()
      bytesread = bytesread+len(l)
    bin = f.read(int(self.header['HEADER_BYTES'])-bytesread)
    l=f.read()
    f.close()
    #now read the data into the array
    (self.dim1,self.dim2)=int(self.header['SIZE1']),int(self.header['SIZE2'])
    if 'little' in self.header['BYTE_ORDER']:
      #test=Numeric.fromstring(l[0:(self.dim1*self.dim2*2)],Numeric.UInt16)
      try:
	 self.data=Numeric.reshape(Numeric.fromstring(l,Numeric.UInt16),[self.dim2, self.dim1])
      except ValueError:
	raise IOError, 'Size spec in ADSC-header does not match size of image data field'
      self.bytecode=Numeric.UInt16
      if verbose: print 'using low byte first (x386-order)'
    else:
      try:
	self.data=Numeric.reshape(Numeric.fromstring(l,Numeric.UInt16),[self.dim2, self.dim1]).byteswapped()
      except ValueError:
	raise IOError, 'Size spec in ADSC-header does not match size of image data field'
      self.bytecode=Numeric.UInt16
      if verbose: print 'using high byte first (network order)'
    self.resetvals()
    return self

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
      print 'adscimage.add() called with something that does not have a data field'
    try:
      self.data=Numeric.clip(self.data+otherImage.data,0,65535)
    except:
      message='incompatible images - Do they have the same size?'
      
  def resetvals(self):
    self.m=self.stddev=self.maxval=self.minval=None
  
  def rebin(self,x_rebin_fact,y_rebin_fact):
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
  I=adscimage()
  b=time.clock()
  while (sys.argv[1:]):
    I.read(sys.argv[1])
    r=I.toPIL16()
    I.rebin(2,2)
    I.write('jegErEnFil0000.img')
    print sys.argv[1] + (": max=%d, min=%d, mean=%.2e, stddev=%.2e") % (I.getmax(),I.getmin(), I.getmean(), I.getstddev()) 
    print 'integrated intensity (%d %d %d %d) =%.3f' % (10,20,20,40,I.integrate_area((10,20,20,40)))
    sys.argv[1:]=sys.argv[2:]
  e=time.clock()
  print (e-b)
