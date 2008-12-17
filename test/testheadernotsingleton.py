
import os, shutil, unittest
from fabio.openimage import openimage

class testheadernotsingleton(unittest.TestCase):
    def testheader(self):
        file1 = os.path.join("testimages", "mb_LP_1_001.img")
        file2 = os.path.join("testimages", "mb_LP_1_002.img")
        self.assertTrue( os.path.exists(file1))
        if not os.path.exists(file2):
            shutil.copy(file1, file2)
        image1 = openimage(file1)
        image2 = openimage(file2)
        # print i1.header, i2.header
        self.assertEqual( image1.header['filename'] , file1 )
        self.assertEqual( image2.header['filename'] , file2 )
        self.assertNotEqual( image1.header['filename'] , 
                             image2.header['filename'] )

if __name__ == "__main__":
    unittest.main()
