

# Unit tests

""" Test the fit2d mask reader """


from fabio.fit2dmaskimage import fit2dmaskimage
from fabio.edfimage import edfimage

import unittest, Numeric

class testfacemask(unittest.TestCase):
    """ test the picture of a face """
    filename = "testimages/face.msk"
    edffilename = "testimages/face.edf.gz"
    def test_getmatch(self):
        """ test edf and msk are the same """
        i = fit2dmaskimage()
        i.read(self.filename)
        j = edfimage()
        j.read(self.edffilename)
        # print "edf: dim1",oe.dim1,"dim2",oe.dim2
        self.assertEqual(i.dim1, j.dim1)
        self.assertEqual(i.dim2, j.dim2)
        self.assertEqual(i.data.shape, j.data.shape)
        diff = j.data - i.data
        sumd  = Numeric.sum(Numeric.ravel(diff).astype(Numeric.Float32))
        self.assertEqual( sumd , 0 )

class testclickedmask(unittest.TestCase):
    """ A few random clicks to make a test mask """
    filename = "testimages/fit2d_click.msk"
    edffilename = "testimages/fit2d_click.edf.gz"

    def test_read(self):
        """ Check it reads a mask OK """
        i = fit2dmaskimage()
        i.read(self.filename)
        self.assertEqual(i.dim1 , 1024)
        self.assertEqual(i.dim2 , 1024)
        self.assertEqual(i.bpp , 1 )
        self.assertEqual(i.bytecode, Numeric.UInt8)
        self.assertEqual(i.data.shape, (1024, 1024) )

    def test_getmatch(self):
        """ test edf and msk are the same """
        i = fit2dmaskimage()
        j = edfimage()
        i.read(self.filename)
        j.read(self.edffilename)
        self.assertEqual(i.data.shape, j.data.shape)
        diff = j.data - i.data
        self.assertEqual(i.getmax(), 1)
        self.assertEqual(i.getmin(), 0)
        sumd  = Numeric.sum(Numeric.ravel(diff).astype(Numeric.Float32))
        self.assertEqual( sumd , 0 )

    
        
if __name__ == "__main__":
    unittest.main()
        
        
        
  
