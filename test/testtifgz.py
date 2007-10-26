

import unittest, os

from fabio.openimage import openimage

class testgziptif(unittest.TestCase):
    def setUp(self):
        self.zipped = os.path.join("testimages",
                                   "oPPA_5grains_0001.tif.gz")
        self.unzipped = os.path.join("testimages",
                                     "oPPA_5grains_0001.tif")
        os.system("gunzip -c %s > %s" % (self.zipped, self.unzipped))
        assert os.path.exists(self.zipped)
        assert os.path.exists(self.unzipped)        
    
    def test1(self):
        o1 = openimage(self.zipped)
        o2 = openimage(self.unzipped)
        self.assertEqual(o1.data[0,0],10)
        self.assertEqual(o2.data[0,0],10)

    def tearDown(self):
        os.remove(self.unzipped)

class testtif_rect(unittest.TestCase):
    def test1(self):
        o1 = openimage(os.path.join("testimages",
                                    "testmap1_0002.tif.gz"))
        self.assertEqual(o1.data.shape, ( 100, 120 ) )

if __name__ == "__main__":
    unittest.main()
