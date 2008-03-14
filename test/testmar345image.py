
"""
# Unit tests

# builds on stuff from ImageD11.test.testpeaksearch
"""


from fabio.mar345image import mar345image
import unittest, os
# filename dim1 dim2 min max mean stddev
TESTIMAGES = """example.mar2300 2300 2300 0 999999 180.15 4122.67
example.mar2300.bz2 2300 2300 0 999999 180.15 4122.67
example.mar2300.gz  2300 2300 0 999999 180.15 4122.67"""


class testMAR345(unittest.TestCase):
    def test_read(self):
        for line in TESTIMAGES.split("\n"):
            vals = line.split()
            name = vals[0]
            dim1, dim2 = [int(x) for x in vals[1:3]]
            mini, maxi, mean, stddev = [float(x) for x in vals[3:]]
            obj = mar345image()
            obj.read(os.path.join("testimages", name))
            
            self.assertAlmostEqual(mini, obj.getmin(), 2, "getmin")
            self.assertAlmostEqual(maxi, obj.getmax(), 2, "getmax")
            self.assertAlmostEqual(mean, obj.getmean(), 2, "getmean")
            self.assertAlmostEqual(stddev, obj.getstddev(), 2, "getstddev")
            self.assertEqual(dim1, obj.dim1, "dim1")
            self.assertEqual(obj.dim1, obj.dim2, "dim2!=dim1")
            


if __name__ == "__main__":
    unittest.main()
