#!/usr/bin/env python 
"""

Authors: Henning O. Sorensen & Erik Knudsen
         Center for Fundamental Research: Metal Structures in Four Dimensions
         Risoe National Laboratory
         Frederiksborgvej 399
         DK-4000 Roskilde
         email:erik.knudsen@risoe.dk
          + 
         Jon Wright, ESRF, France
"""

from PIL import Image
import Numeric
import struct
import string

class mar345image:
  def __init__(self,filename=None):
    self.data=None
    self.header={}
    self.filename = filename
    self.dim1=self.dim2=0
    self.m=self.maxval=self.stddev=self.minval=None
    self.header_keys=[]
    self.bytecode=None
    if filename:
      self.read(filename)

  def toPIL16(self,filename=None):
    if filename:
      self.read(filename)
    PILimage={
      'f':Image.frombuffer("F",(self.dim1,self.dim2),self.data.astype(Numeric.UInt16),"raw","F;16",0,-1),
      'w':Image.frombuffer("F",(self.dim1,self.dim2),self.data,"raw","F;16",0,-1),
      'u':Image.fromstring("F",(self.dim1,self.dim2),self.data,"raw","F;32N",0,-1),
      }[self.bytecode]
    return PILimage

  def _open(self,fname,mode="rb"):
    try:
      f=open(fname,mode)
    except:
      raise IOError
    return f
 
  def read(self,fname):
    self.filename = fname
    f=self._open(self.filename,"rb")
    self._readheader(f)
 
    try:
      import mar345_io
    except:
      print 'error importing the mar345_io backend - generating empty picture'
      f.close()
      self.dim1=1
      self.dim2=1
      self.bytecode='u'
      self.data=Numeric.resize(Numeric.array([0],'u'),[1,1])
      return self

    if 'compressed' in self.header['Format']:
      self.data=mar345_io.unpack(f,self.dim1,self.dim2,self.numhigh)
    else:
      print "error: cannot handle these formats yet due to lack of documentation"
      return None
    self.bytecode='u'
    f.close()
    return self
  
  def readheader(self,fname):
    f=self._open(fname)
    self._readheader(f)
    f.close()
    return self

  def getheader(self):
    return self.header

  def _readheader(self,infile=None):
    clip = '\x00'
    #using a couple of local variables inside this function  
    f=infile
    h={}

    #header is 4096 bytes long
    l=f.read(64)
    #the contents of the mar345 header is taken to be as described in http://www.mar-usa.com/support/downloads/mar345_formats.pdf
    #the first 64 bytes are 4-byte integers (but in the CBFlib example image it seems to 128 bytes?)
    #first 4-byte integer is a marker to check endianness TODO: turn this into a real check
    if (l[0:4]=='1234'):
      formatstring='L'  
    #image dimensions
    self.dim1=self.dim2=int(struct.unpack('L',l[4:8])[0])
    #number of high intensity pixels
    self.numhigh=struct.unpack('L',l[2*4:(2+1)*4])[0]
    h['NumHigh']=self.numhigh
    #Image format
    i=struct.unpack('L',l[3*4:(3+1)*4])[0]
    print i
    if i==1:
      h['Format']='compressed'
    elif i==2:
      h['Format']='spiral'
    else:
      h['Format']='compressed'
      print "warning: image format could not be detetermined - assuming compressed mar345"
    #collection mode
    h['Mode']={0:'Dose', 1: 'Time'}[struct.unpack('L',l[4*4:(4+1)*4])[0]]
    #total number of pixels
    self.numpixels=struct.unpack('L',l[5*4:(5+1)*4])[0]
    h['NumPixels']=str(self.numpixels)
    #pixel dimensions (length,height) in mm
    h['PixelLength']=struct.unpack('L',l[6*4:(6+1)*4])[0]/1000.0
    h['PixelHeight']=struct.unpack('L',l[7*4:(7+1)*4])[0]/1000.0
    #x-ray wavelength in AA
    h['Wavelength']=struct.unpack('L',l[8*4:(8+1)*4])[0]/1000000.0
    #used distance
    h['Distance']=struct.unpack('L',l[9*4:(9+1)*4])[0]/1000.0
    #starting and ending phi
    h['StartPhi']=struct.unpack('L',l[10*4:11*4])[0]/1000.0
    h['EndPhi']=struct.unpack('L',l[11*4:12*4])[0]/1000.0
    #starting and ending omega
    h['StartOmega']=struct.unpack('L',l[12*4:13*4])[0]/1000.0
    h['EndOmega']=struct.unpack('L',l[13*4:14*4])[0]/1000.0
    #Chi and Twotheta angles
    h['Chi']=struct.unpack('L',l[14*4:15*4])[0]/1000.0
    h['TwoTheta']=struct.unpack('L',l[15*4:16*4])[0]/1000.0
    
    #the rest of the header is ascii
    l=f.read(128)
    if not 'mar research' in l:
      print "warning: the string \"mar research\" should be in bytes 65-76 of the header but was not"
    l=string.strip(f.read(4096-128-64))
    for m in l.splitlines():
      if m=='END OF HEADER': break
      n=m.split(' ',1)
      if n[0]=='':
        continue
      if n[0] in ('PROGRAM','DATE','SCANNER','HIGH','MULTIPLIER','GAIN','WAVELENGTH','DISTANCE','RESOLUTION','CHI','TWOTHETA','MODE','TIME','GENERATOR','MONOCHROMATOR','REMARK'):
        h[n[0]]=n[1].strip()
        continue
      if n[0] in ('FORMAT'):
        (h['DIM'],h['FORMAT_TYPE'],h['NO_PIXELS'])=n[1].split()
        continue
      if n[0] in ('PIXEL','OFFSET','PHI','OMEGA','COUNTS','CENTER','INTENSITY','HISTOGRAM','COLLIMATOR'):
        n=m.split()
        h.update( [(n[0]+'_'+n[j],n[j+1]) for j in range(1,len(n),2)] )
        continue
    self.header=h
    return h

  def write(self):
    pass
  
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
   
  def rebin(self,x_rebin_factor, y_rebin_factor):
    print "rebinning not implemented - yet!"

if __name__=='__main__':
  import sys
  i=mar345image()
  i.read(sys.argv[1])
  i2=i.toPIL16()
  i2.show()
  print i.header
