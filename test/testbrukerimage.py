#Unit tests

#built on testedfimage
import unittest,os,Numeric
from fabio import brukerimage


#this is actually a violation of the bruker format since the order of the header items is specified
#in the standard, whereas the order of a python dictionary is not  
myheader={"FORMAT":'86', 'NPIXELB':'2','VERSION':'9','HDRBLKS':'5','NOVERFL':'4', 'NCOLS':'256','NROWS':'256','WORDORD':'0'};

myimage = Numeric.ones((256,256), Numeric.UInt16, savespace=1)*16
myimage[0,0]=0
myimage[1,1]=32
myimage[127:129,127:129]=65535

overflows=[
["%09d"% 4194304,("%07d"% (127*256+127))],
["%09d"% 4194304,("%07d"% (127*256+128))],
["%09d"% 4194304,("%07d"% (128*256+127))],
["%09d"% 4194304,("%07d"% (128*256+128))],
]

class testbruker(unittest.TestCase):
  filename = 'image.0000'
  
  def setUp(self):
    f=open("image.0000",'wb')
    wrb=0
    for k,v in myheader.iteritems():
      f.write(("%-7s" % k) + ':' + ("%-72s" % v))
      wrb=wrb+80
    hdrblks=int(myheader['HDRBLKS'])
    while (wrb<hdrblks*512):
      f.write("\x1a\x04")
      f.write('.'*78)
      wrb=wrb+80
    f.write(myimage.tostring())
    
    noverfl=int(myheader['NOVERFL'])
    for o in overflows:
      f.write(o[0]+o[1])
    f.write('.'*(512 - (16*noverfl)%512))

  def tearDown(self):
    try:
      os.system("rm image.0000")
    except:
      pass
  
  def test_read(self):
    o = brukerimage()
    o.read(self.filename)
    self.assertAlmostEqual( o.getmean() , 272.0,2 )
    self.assertEqual( o.getmin() ,   0 )
    self.assertEqual( o.getmax() ,  4194304 )

class testbzipbruker(testbruker):
    filename = "image.0000.bz2"
    def setUp(self):
        testbruker.setUp(self)
        os.system("bzip2 image.0000")
    def tearDown(self):
        try: os.remove(self.filename)
        except: pass

class testgzipbruker(testbruker):
    filename = "image.0000.gz"
    def setUp(self):
        testbruker.setUp(self)
        os.system("gzip image.0000")
    def tearDown(self):
        try: os.remove(self.filename)
        except: pass

if __name__=="__main__":
  unittest.main()
