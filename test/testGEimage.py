
"""
# Unit tests

# builds on stuff from ImageD11.test.testpeaksearch
"""


from fabio.GEimage import GEimage
import unittest, os
# filename dim1 dim2 min max mean stddev
TESTIMAGES = """GE_aSI_detector_image_1529  2048 2048 1515 16353 1833.0311 56.9124
GE_aSI_detector_image_1529.gz  2048 2048 1515 16353 1833.0311 56.9124
GE_aSI_detector_image_1529.bz2  2048 2048 1515 16353 1833.0311 56.9124"""


class testGE(unittest.TestCase):
    def test_read(self):
        for line in TESTIMAGES.split("\n"):
            vals = line.split()
            name = vals[0]
            dim1, dim2 = [int(x) for x in vals[1:3]]
            mini, maxi, mean, stddev = [float(x) for x in vals[3:]]
            obj = GEimage()
            obj.read(os.path.join("testimages", name))
            
            self.assertAlmostEqual(mini, obj.getmin(), 2, "getmin")
            self.assertAlmostEqual(maxi, obj.getmax(), 2, "getmax")
            self.assertAlmostEqual(mean, obj.getmean(), 2, "getmean")
            self.assertAlmostEqual(stddev, obj.getstddev(), 2, "getstddev")
            self.assertEqual(dim1, obj.dim1, "dim1")
            self.assertEqual(dim2, obj.dim2, "dim2")
            


if __name__ == "__main__":
    unittest.main()
