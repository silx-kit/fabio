

# Unit tests

# builds on stuff from ImageD11.test.testpeaksearch

from fabio import marccdimage

import unittest, Numeric, os


# filename dim1 dim2 min max mean stddev
ims = """corkcont2_H_0089.mccd  2048 2048  0  354  7.2611 14.639
corkcont2_H_0089.mccd.bz2 2048 2048  0  354  7.2611 14.639
corkcont2_H_0089.mccd.gz 2048 2048  0  354  7.2611 14.639
somedata_0001.mccd 1024 1024  0  20721  128.37 136.23
somedata_0001.mccd.bz2 1024 1024  0  20721  128.37 136.23
somedata_0001.mccd.gz 1024 1024  0  20721  128.37 136.23"""


class testflatmccds(unittest.TestCase):
        
           
    def test_read(self):
        for line in ims.split("\n"):
            vals = line.split()
            name = vals[0]
            dim1, dim2 = [int(x) for x in vals[1:3]]
            mini, maxi, mean, stddev = [float(x) for x in vals[3:]]
            o = marccdimage()
            o.read(os.path.join("testimages",name))
            self.assertAlmostEqual(mini, o.getmin(), 2, "getmin")
            self.assertAlmostEqual(maxi, o.getmax(), 2, "getmax")
            self.assertAlmostEqual(mean, o.getmean(), 2, "getmean")
            self.assertAlmostEqual(stddev, o.getstddev(), 2, "getstddev")
            self.assertEqual(dim1, o.dim1, "dim1")
            self.assertEqual(dim1, o.dim2, "dim2")
            
        


        
if __name__=="__main__":
    unittest.main()
        
        
        
  