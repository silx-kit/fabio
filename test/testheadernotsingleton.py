
import os, shutil, unittest
from fabio.openimage import openimage

class testheadernotsingleton(unittest.TestCase):
    def testheader(self):
        f1 = os.path.join("testimages", "mb_LP_1_001.img")
        f2 = os.path.join("testimages", "mb_LP_1_002.img")
        self.assertTrue( os.path.exists(f1))
        if not os.path.exists(f2):
            shutil.copy(f1, f2)
        i1 = openimage(f1)
        i2 = openimage(f2)
        # print i1.header, i2.header
        self.assertEqual( i1.header['filename'] , f1 )
        self.assertEqual( i2.header['filename'] , f2 )
        self.assertNotEqual( i1.header['filename'] , i2.header['filename'] )

if __name__=="__main__":
    unittest.main()
