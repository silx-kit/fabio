

"""
# Unit tests

# builds on stuff from ImageD11.test.testpeaksearch
"""
from fabio.adscimage import adscimage
from fabio.edfimage import edfimage
import unittest, os
import Numeric

# statistics come from fit2d I think
# filename dim1 dim2 min max mean stddev
TESTIMAGES = """mb_LP_1_001.img 3072 3072 0.0000 65535. 120.33 147.38 
mb_LP_1_001.img.gz  3072 3072 0.0000 65535.  120.33 147.38 
mb_LP_1_001.img.bz2 3072 3072 0.0000 65535.  120.33 147.38 """




class testmatch(unittest.TestCase):
    """ check the fit2d conversion to edf gives same numbers """
    def setUp(self):
        """ make the image """
        if not os.path.exists("testimages/mb_LP_1_001.img"):
            raise Exception("Get testimages/mb_LP_1_001.img")
        if not os.path.exists("testimages/mb_LP_1_001.edf"):
            raise Exception("make testimages/mb_LP_1_001.edf")

    def testsame(self):
        """match to edf"""
        im1 = edfimage()
        im1.read("testimages/mb_LP_1_001.edf")
        im2 = adscimage()
        im2.read("testimages/mb_LP_1_001.img")
        diff = (im1.data - im2.data).flat
        self.assertAlmostEqual(Numeric.maximum.reduce(diff), 0, 2)
        self.assertAlmostEqual(Numeric.minimum.reduce(diff), 0, 2)

class testflatmccdsadsc(unittest.TestCase):
    """
    Read some test images on jon's disk
    FIXME: upload to sourceforge and add a setUp with wget?
    """           
    def test_read(self):
        """ check we can read these images"""
        for line in TESTIMAGES.split("\n"):
            vals = line.split()
            name = vals[0]
            dim1, dim2 = [int(x) for x in vals[1:3]]
            mini, maxi, mean, stddev = [float(x) for x in vals[3:]]
            obj = adscimage()
            obj.read(os.path.join("testimages", name))
            self.assertAlmostEqual(mini, obj.getmin(), 2, "getmin")
            self.assertAlmostEqual(maxi, obj.getmax(), 2, "getmax")
            self.assertAlmostEqual(mean, obj.getmean(), 2, "getmean")
            self.assertAlmostEqual(stddev, obj.getstddev(), 2, "getstddev")
            self.assertEqual(dim1, obj.dim1, "dim1")
            self.assertEqual(dim2, obj.dim2, "dim2")
            
        


        
if __name__ == "__main__":
    unittest.main()
        
        
        
