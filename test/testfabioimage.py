
from fabio import fabioimage
import unittest

import Numeric

class test50000(unittest.TestCase):
    def setUp(self):
        d = Numeric.ones((1024,1024), Numeric.UInt16)
        d = (d*50000).astype(Numeric.UInt16)
        assert d.typecode() == Numeric.ones((1),Numeric.UInt16).typecode()
        h = {"Title":"50000 everywhere"}
        self.o = fabioimage(d,h)
      
    def testGetMax(self):
        self.assertEqual( self.o.getmax(), 50000)

    def testGetMin(self):
        self.assertEqual( self.o.getmin(), 50000)
    
    def testGetMean(self):
        self.assertEqual( self.o.getmean(), 50000)
        
    def getstddev(self):
        self.assertEqual( self.o.getstddev(), 0)
        
class testslices(unittest.TestCase):
    def setUp(self):
        d2 = Numeric.zeros((1024,1024), Numeric.UInt16, savespace = 1 )
        h = {"Title":"zeros and 100"}
        self.c = [ 256, 256, 790, 768 ]
        self.o = fabioimage(d2, h)
        self.s = s = self.o.make_slice(self.c)
        # Note - d2 is modified *after* fabioimage is made
        d2[s] = d2[s] + 100
        assert self.o.maxval is None
        assert self.o.minval is None
        self.npix = (s[0].stop-s[0].start)*(s[1].stop-s[1].start)
        
    def testGetMax(self):
        self.assertEqual( self.o.getmax(), 100)

    def testGetMin(self):
        self.assertEqual( self.o.getmin(), 0)
        
    def testIntegrateArea(self):
        self.o.resetvals()
        a1 = self.o.integrate_area(self.c) 
        self.o.resetvals()
        a2 = self.o.integrate_area(self.s)
        self.assertEqual(a1,a2)
        self.assertEqual(a1,self.npix*100)
        
    
class test_open(unittest.TestCase):


    def tearDown(self):
        import os
        for name in ["testfile","testfile.gz", "testfile.bz2"]:
            try:
                os.remove(name)
            except:
                pass
            
    def setUp(self):
        import os
        open("testfile","wb").write("{ hello }")
        os.system("gzip testfile")
        open("testfile","wb").write("{ hello }")
        os.system("bzip2 testfile")
        open("testfile","wb").write("{ hello }")
        self.o = fabioimage()

    def testFlat(self):
        r = self.o._open("testfile").read()
        self.assertEqual( r , "{ hello }" ) 

    def testGz(self):
        r = self.o._open("testfile.gz").read()
        self.assertEqual( r , "{ hello }" ) 
    
    def testBz2(self):    
        r = self.o._open("testfile.bz2").read()
        self.assertEqual( r , "{ hello }" ) 
    
if __name__=="__main__":
    unittest.main()