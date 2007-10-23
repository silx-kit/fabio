
"""
#bruker Unit tests

#built on testedfimage
"""
import unittest, os
import numpy.oldnumeric as Numeric
from fabio.brukerimage import brukerimage


#this is actually a violation of the bruker format since the order of
# the header items is specified
#in the standard, whereas the order of a python dictionary is not
MYHEADER = {"FORMAT":'86', 
            'NPIXELB':'2',
            'VERSION':'9',
            'HDRBLKS':'5',
            'NOVERFL':'4', 
            'NCOLS':'256',
            'NROWS':'256',
            'WORDORD':'0'}

MYIMAGE = Numeric.ones((256, 256), Numeric.UInt16, savespace  = 1) * 16
MYIMAGE[0, 0] = 0
MYIMAGE[1, 1] = 32
MYIMAGE[127:129, 127:129] = 65535

OVERFLOWS = [
    ["%09d" % 4194304, ("%07d" % (127 * 256 + 127))],
    ["%09d" % 4194304, ("%07d" % (127 * 256 + 128))],
    ["%09d" % 4194304, ("%07d" % (128 * 256 + 127))],
    ["%09d" % 4194304, ("%07d" % (128 * 256 + 128))]
    ]

class testbruker(unittest.TestCase):
    """basic test"""
    filename = 'image.0000'

    def setUp(self):
        """ Generate a test bruker image """
        fout = open("image.0000", 'wb')
        wrb = 0
        for key, val in MYHEADER.iteritems():
            fout.write(("%-7s" % key) + ':' + ("%-72s" % val))
            wrb = wrb + 80
        hdrblks = int(MYHEADER['HDRBLKS'])
        while (wrb < hdrblks * 512):
            fout.write("\x1a\x04")
            fout.write('.'*78)
            wrb = wrb + 80
        fout.write(MYIMAGE.tostring())

        noverfl = int(MYHEADER['NOVERFL'])
        for ovf in OVERFLOWS:
            fout.write(ovf[0] + ovf[1])
        fout.write('.' * (512 - (16* noverfl)% 512))

    def tearDown(self):
        """ clean up """
        if os.path.exists(self.filename):
            os.remove(self.filename)

    def test_read(self):
        """ see if we can read the test image """
        obj = brukerimage()
        obj.read(self.filename)
        self.assertAlmostEqual( obj.getmean() , 272.0, 2 )
        self.assertEqual( obj.getmin() ,   0 )
        self.assertEqual( obj.getmax() ,  4194304 )

class testbzipbruker(testbruker):
    """ test for a bzipped image """
    def setUp(self):
        """ create the image """
        testbruker.setUp(self)
        os.system("bzip2 %s" % (self.filename))
        self.filename += ".bz2"
        # tear down is inherited and self.filename will be removed

class testgzipbruker(testbruker):
    """ test for a gzipped image """
    def setUp(self):
        """ Create the image """
        testbruker.setUp(self)
        os.system("gzip %s" % (self.filename))
        self.filename += ".gz"
        # tear down is inherited and self.filename will be removed




# statistics come from fit2d I think
# filename dim1 dim2 min max mean stddev

TESTIMAGES = """Cr8F8140k103.0026   512  512  0  145942 289.37  432.17 
Cr8F8140k103.0026.gz   512  512  0  145942 289.37  432.17 
Cr8F8140k103.0026.bz2   512  512  0 145942 289.37  432.17 """


class test_real_im(unittest.TestCase):
    """ check some read data as for mar ccd """
          
    def test_read(self):
        """ check we can read these images"""
        for line in TESTIMAGES.split("\n"):
            vals = line.split()
            name = vals[0]
            dim1, dim2 = [int(x) for x in vals[1:3]]
            mini, maxi, mean, stddev = [float(x) for x in vals[3:]]
            obj = brukerimage()
            obj.read(os.path.join("testimages", name))
            self.assertAlmostEqual(mini, obj.getmin(), 2, "getmin")
            self.assertAlmostEqual(maxi, obj.getmax(), 2, "getmax")
            self.assertAlmostEqual(mean, obj.getmean(), 2, "getmean")
            self.assertAlmostEqual(stddev, obj.getstddev(), 2, "getstddev")
            self.assertEqual(dim1, obj.dim1, "dim1")
            self.assertEqual(dim2, obj.dim2, "dim2")
            

if __name__ == "__main__":
    unittest.main()
