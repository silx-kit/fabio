

"""
# Unit tests

# builds on stuff from ImageD11.test.testpeaksearch
"""
from fabio import marccdimage

import unittest, os

# statistics come from fit2d I think
# filename dim1 dim2 min max mean stddev
TESTIMAGES = """corkcont2_H_0089.mccd  2048 2048  0  354  7.2611 14.639
corkcont2_H_0089.mccd.bz2 2048 2048  0  354  7.2611 14.639
corkcont2_H_0089.mccd.gz 2048 2048  0  354  7.2611 14.639
somedata_0001.mccd 1024 1024  0  20721  128.37 136.23
somedata_0001.mccd.bz2 1024 1024  0  20721  128.37 136.23
somedata_0001.mccd.gz 1024 1024  0  20721  128.37 136.23"""


class testflatmccds(unittest.TestCase):
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
            obj = marccdimage()
            obj.read(os.path.join("testimages", name))
            self.assertAlmostEqual(mini, obj.getmin(), 2, "getmin")
            self.assertAlmostEqual(maxi, obj.getmax(), 2, "getmax")
            self.assertAlmostEqual(mean, obj.getmean(), 2, "getmean")
            self.assertAlmostEqual(stddev, obj.getstddev(), 2, "getstddev")
            self.assertEqual(dim1, obj.dim1, "dim1")
            self.assertEqual(dim2, obj.dim2, "dim2")
            
        


        
if __name__ == "__main__":
    unittest.main()
        
        
        
