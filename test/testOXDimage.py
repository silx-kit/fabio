
"""
# Unit tests

# builds on stuff from ImageD11.test.testpeaksearch
"""


from fabio.OXDimage import OXDimage
import unittest, os
# filename dim1 dim2 min max mean stddev values are from OD Sapphire 3.0 
TESTIMAGES = """b191_1_9_1_uncompressed.img  512 512 -500 11975 25.70 90.2526
b191_1_9_1_uncompressed.img  512 512 -500 11975 25.70 90.2526"""


class testOXD(unittest.TestCase):
    def test_read(self):
        for line in TESTIMAGES.split("\n"):
            vals = line.split()
            name = vals[0]
            dim1, dim2 = [int(x) for x in vals[1:3]]
            mini, maxi, mean, stddev = [float(x) for x in vals[3:]]
            obj = OXDimage()
            obj.read(os.path.join("testimages", name))
            
            self.assertAlmostEqual(mini, obj.getmin(), 2, "getmin")
            self.assertAlmostEqual(maxi, obj.getmax(), 2, "getmax")
            self.assertAlmostEqual(mean, obj.getmean(), 2, "getmean")
            self.assertAlmostEqual(stddev, obj.getstddev(), 2, "getstddev")
            self.assertEqual(dim1, obj.dim1, "dim1")
            self.assertEqual(dim2, obj.dim2, "dim2")


if __name__ == "__main__":
    unittest.main()
