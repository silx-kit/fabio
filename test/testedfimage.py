

"""
# Unit tests

# builds on stuff from ImageD11.test.testpeaksearch
"""
from fabio import edfimage

import unittest, Numeric, os

MYHEADER = "{\n%-1020s}\n" % (
"""Omega = 0.0 ; 
Dim_1 = 256 ;
Dim_2 = 256 ;
DataType = FloatValue ;
ByteOrder = LowByteFirst ;
Image = 1;
History-1 = something=something else;
\n\n""")

MYIMAGE = Numeric.ones((256, 256), Numeric.Float32, savespace = 1)*10
MYIMAGE[0, 0] = 0
MYIMAGE[1, 1] = 20

assert len(MYIMAGE[0:1, 0:1].tostring()) == 4,  \
    len(MYIMAGE[0:1, 0:1].tostring())

class testflatedfs(unittest.TestCase):
    """ test some flat images """
    filename = "im0000.edf"
    
    def setUp(self):
        """ initialise"""
        outf = open(self.filename, "wb")
        assert len(MYHEADER) % 1024 == 0
        outf.write(MYHEADER)
        outf.write(MYIMAGE.tostring())
        outf.close()
        
    def tearDown(self):
        """ clean up """
        if os.path.exists(self.filename):
            os.remove(self.filename)
    
    def test_read(self):
        """ check readable"""
        obj = edfimage()
        obj.read(self.filename)
        self.assertEqual(obj.dim1 , 256)
        self.assertEqual(obj.dim2 , 256)
        self.assertEqual(obj.bpp , 4 )
        self.assertEqual(obj.bytecode, Numeric.Float32)
        self.assertEqual(obj.data.shape, (256, 256) )
        self.assertEqual(obj.header['History-1'],
                         "something=something else" )
        
    def test_getstats(self):
        """ test statistics"""
        obj = edfimage()
        obj.read(self.filename)
        self.assertEqual( obj.getmean() , 10 )
        self.assertEqual( obj.getmin() ,   0 )
        self.assertEqual( obj.getmax() ,  20 )
    
class testbzipedf(testflatedfs):
    """ same for bzipped versions """
    def setUp(self):
        """set it up"""
        testflatedfs.setUp(self)
        os.system("bzip2 %s"%(self.filename))
        self.filename += ".bz2"
        # self.filename will be the file to be removed

class testgzipedf(testflatedfs):
    """ same for gzipped versions """
    def setUp(self):
        """ set it up """
        testflatedfs.setUp(self)
        os.system("gzip %s" % (self.filename)) 
        self.filename += ".gz"
        # self.filename will be the file to be removed

        
if __name__ == "__main__":
    unittest.main()
        
        
        
  
