import Numeric
import math
from PIL import Image
import os
import brukerimage

class bruker100image(brukerimage.brukerimage):
  
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
    try:
      self._readheader(f)
    except:
      raise
    
    rows   =int(self.header['NROWS'])
    cols   =int(self.header['NCOLS'])
    npixelb=int(self.header['NPIXELB'][0])   # you had to read the Bruker docs to know this!
    
    # We are now at the start of the image - assuming readbrukerheader worked
    size=rows*cols*npixelb
    self.data=self.readbytestream(f,f.tell(),rows,cols,npixelb,datatype="int",signed='n',swap='n')

    noverfl=self.header['NOVERFL'].split() # now process the overflows
    #read the set of "underflow pixels" - these will be completely disregarded for now
    data=self.data
    k=0
    
    while k<2:#for the time being things - are done in 16 bits
      datatype={'1' : Numeric.UInt8, '2' : Numeric.UInt16, '4' : Numeric.UInt32 }[("%d" % 2**k)]
      ar=Numeric.array(Numeric.fromstring(f.read(int(noverfl[k])*(2**k)),datatype),Numeric.UInt16)
      #insert the the overflow pixels in the image array:
      #this is probably a memory intensive way of doing this - might be done in a more clever way
      lim=2**(8*k)-1
      #generate an array comprising of the indices into data.flat where its value equals lim.
      M=Numeric.compress(Numeric.equal(data.flat,lim),Numeric.arange(rows*cols))
      #now put values from ar into those indices
      Numeric.put(data.flat,M,ar)
	
      padding=16*int(math.ceil(int(noverfl[k])*(2**k)/16.)) - int(noverfl[k])*(2**k)
      f.seek(padding,1)
      print noverfl[k] + " bytes read + %d bytes padding" % padding
      k=k+1
	
    f.close()
    
    (self.dim1,self.dim2)=(rows,cols)
    print self.dim1, self.dim2
    self.resetvals()
    return self

if __name__=='__main__':
  import sys,time
  I=bruker100image()
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

