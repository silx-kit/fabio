#!/usr/bin/env python 
"""

Authors: Henning O. Sorensen & Erik Knudsen
         Center for Fundamental Research: Metal Structures in Four Dimensions
         Risoe National Laboratory
         Frederiksborgvej 399
         DK-4000 Roskilde
         email:henning.sorensen@risoe.dk

"""

from PIL import Image
import Numeric
import edfimage

class pnmimage(edfimage.edfimage):
  def __init__(self):
    self.data=None
    self.header={'Subformat':'P5'}
    self.dim1=self.dim2=0
    self.m=self.maxval=self.stddev=self.minval=None
    self.header_keys=self.header.keys()
    self.bytecode=None
 
  def read(self,fname,verbose=0):
    #read the (3 line header)
    f=open(fname,"rb")
    
    self.header_keys=['Subformat','Dimensions','Maxval']
    #1st line contains the pnm image sub format
    #2nd line contains the image pixel dimension
    #3rd line contains the maximum pixel value (at least for grayscale - check this)
    for k in self.header_keys:
      l=f.readline()
      while(l[0]=='#'): l=f.readline()
      self.header[k]=l.strip()
    #set the dimensions
    dims=(self.header['Dimensions'].split())
    self.dim1,self.dim2=int(dims[0]),int(dims[1])
    #figure out how many bytes are used to store the data
    #case construct here!
    m=int(self.header['Maxval'])
    if m<256:
      self.bytecode=Numeric.UInt8
    elif m<65536:
      self.bytecode=Numeric.UInt16
    elif m<2147483648L:
      self.bytecode=Numeric.UInt32
      warn('32-bit pixels are not really supported by the netpgm standard')
    else:
      raise IOError, 'could not figure out what kind of pixels you have'
    #read the image data
    try:
      #let the Subformat header field pick the right decoder
      self.data=eval('self.'+self.header['Subformat']+'dec(f,self.bytecode)')
    except ValueError:
      raise IOError
    self.resetvals()
    return self
    
  def P1dec(self,buf,bytecode):
    warn('single bit images is not supported - yet')
  
  def P3dec(self,buf,bytecode):
    warn('single bit images is not supported - yet')
  
  def P2dec(self,buf,bytecode):
    data=Numeric.zeros((self.dim2,self.dim1))
    i=0
    for l in buf.readlines():
      try:
	data[i,:]=Numeric.array(l.split()).astype(bytecode)
      except ValueError:
	raise IOError, 'Size spec in pnm-header does not match size of image data field'
    return data
  
  def P5dec(self,buf,bytecode):
    l=buf.read()
    try:
      data=Numeric.reshape(Numeric.fromstring(l,bytecode),[self.dim2, self.dim1]).byteswapped()
    except ValueError:
      raise IOError, 'Size spec in pnm-header does not match size of image data field'
    return data

  def write(filename):
    warn('write pnm images is not implemented yet.')
