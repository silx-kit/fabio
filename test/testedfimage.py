

# Unit tests

# builds on stuff from ImageD11.test.testpeaksearch

from fabio import edfimage

import unittest, Numeric, os

myheader = "{\n%-1020s}\n" % (
"""Omega = 0.0 ; 
Dim_1 = 256 ;
Dim_2 = 256 ;
DataType = FloatValue ;
ByteOrder = LowByteFirst ;
Image = 1;
History-1 = something=something else;
\n\n""")

myimage = Numeric.ones((256,256), Numeric.Float32, savespace = 1)*10
myimage[0,0] = 0
myimage[1,1] = 20

assert len(myimage[0:1,0:1].tostring()) == 4,len(myimage[0:1,0:1].tostring())

class testflatedfs(unittest.TestCase):
    filename = "im0000.edf"
    
    def setUp(self):
        f=open("im0000.edf","wb")
        assert len(myheader)%1024 == 0
        f.write(myheader)
        f.write(myimage.tostring())
        f.close()
        
    def tearDown(self):
        try: os.remove(self.filename)
        except: pass
    
    def test_read(self):
        o = edfimage()
        o.read(self.filename)
        self.assertEqual(o.dim1 , 256)
        self.assertEqual(o.dim2 , 256)
        self.assertEqual(o.bpp , 4 )
        self.assertEqual(o.bytecode, Numeric.Float32)
        self.assertEqual(o.data.shape, (256,256) )
        self.assertEqual(o.header['History-1'],
                         "something=something else" )
        
    def test_getstats(self):
        o = edfimage()
        o.read(self.filename)
        self.assertEqual( o.getmean() , 10 )
        self.assertEqual( o.getmin() ,   0 )
        self.assertEqual( o.getmax() ,  20 )
    
class testbzipedf(testflatedfs):
    filename = "im0000.edf.bz2"
    def setUp(self):
        testflatedfs.setUp(self)
        os.system("bzip2 im0000.edf") 
    def tearDown(self):
        testflatedfs.tearDown(self)
        try: os.remove(self.filename)
        except: pass

class testgzipedf(testflatedfs):
    filename = "im0000.edf.gz"
    def setUp(self):
        testflatedfs.setUp(self)
        os.system("gzip im0000.edf") 
    def tearDown(self):
        testflatedfs.tearDown(self)
        try: os.remove(self.filename)
        except: pass
            
        
if __name__=="__main__":
    unittest.main()
        
        
        
  