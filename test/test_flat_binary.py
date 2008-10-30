

import unittest, os
import fabio.openimage

class test_flat_binary(unittest.TestCase):
    filename = "binary_1234.dat"
    def setUp(self):
        f = open(self.filename,"wb")
        # A 2048 by 2048 blank image
        f.write("\0x0"*2048*2048*2)
        f.close()
    def test_openimage(self):
        im = fabio.openimage.openimage( self.filename )
        assert im.data.tostring() == "\0x0"*2048*2048*2, "Failed"
    def tearDown(self):
        os.remove(self.filename)

if __name__=="__main__":
    unittest.main()
