

import unittest, os


from fabio.openimage import openimage


from fabio.edfimage import edfimage

class testopenedf(unittest.TestCase):
    """openimage opening edf"""
    fname = os.path.join("testimages","F2K_Seb_Lyso0675.edf")
    def setUp(self):
        """ check file exists """
        if not os.path.exists(self.fname):
            raise Exception("You need " + self.fname + "for this test")
    def testcase(self):
        """ check we can read it"""
        obj = openimage(self.fname)
        obj2 = edfimage()
        obj2.read(self.fname)
        self.assertEqual(obj.data[10, 10], obj2.data[10, 10])
        self.assertEqual( type(obj), type(obj2) )
        # etc

class testedfgz(testopenedf):
    """openimage opening edf gzip"""
    fname = os.path.join("testimages","F2K_Seb_Lyso0675.edf.gz")

class testedfbz2(testopenedf):
    """openimage opening edf bzip"""
    fname = os.path.join("testimages","F2K_Seb_Lyso0675.edf.bz2")
    

from fabio.marccdimage import marccdimage

class testopenmccd(unittest.TestCase):
    """openimage opening mccd"""
    fname = os.path.join("testimages","somedata_0001.mccd")
    def setUp(self):
        """ check file exists """
        if not os.path.exists(self.fname):
            raise Exception("You need " + self.fname + "for this test")
    def testcase(self):
        """ check we can read it"""
        obj = openimage(self.fname)
        obj2 = marccdimage()
        obj2.read(self.fname)
        self.assertEqual(obj.data[10, 10], obj2.data[10, 10])
        self.assertEqual( type(obj), type(obj2) )
        # etc

class testmccdgz(testopenmccd):
    """openimage opening mccd gzip"""
    fname = os.path.join("testimages","somedata_0001.mccd.gz")


class testmccdbz2(testopenmccd):
    """openimage opening mccd bzip"""
    fname = os.path.join("testimages","somedata_0001.mccd.bz2")




from fabio.fit2dmaskimage import fit2dmaskimage

class testmask(unittest.TestCase):
    """openimage opening mccd"""
    fname = os.path.join("testimages","face.msk")
    def setUp(self):
        """ check file exists """
        if not os.path.exists(self.fname):
            raise Exception("You need " + self.fname + "for this test")
    def testcase(self):
        """ check we can read it"""
        obj = openimage(self.fname)
        obj2 = fit2dmaskimage()
        obj2.read(self.fname)
        self.assertEqual(obj.data[10, 10], obj2.data[10, 10])
        self.assertEqual( type(obj), type(obj2) )
        # etc

class testmaskgz(testmask):
    """openimage opening mccd gzip"""
    fname = os.path.join("testimages","face.msk.gz")

class testmaskbz2(testmask):
    """openimage opening mccd bzip"""
    fname = os.path.join("testimages","face.msk.bz2")




from fabio.brukerimage import brukerimage

class testbruker(unittest.TestCase):
    """openimage opening bruker"""
    fname = os.path.join("testimages","Cr8F8140k103.0026")
    def setUp(self):
        """ check file exists """
        if not os.path.exists(self.fname):
            raise Exception("You need " + self.fname + "for this test")
    def testcase(self):
        """ check we can read it"""
        obj = openimage(self.fname)
        obj2 = brukerimage()
        obj2.read(self.fname)
        self.assertEqual(obj.data[10, 10], obj2.data[10, 10])
        self.assertEqual( type(obj), type(obj2) )
        # etc

class testbrukergz(testbruker):
    """openimage opening bruker gzip"""
    fname = os.path.join("testimages","Cr8F8140k103.0026.gz")

class testbrukerbz2(testbruker):
    """openimage opening bruker bzip"""
    fname = os.path.join("testimages","Cr8F8140k103.0026.bz2")



from fabio.adscimage import adscimage

class testadsc(unittest.TestCase):
    """openimage opening adsc"""
    fname = os.path.join("testimages","mb_LP_1_001.img")
    def setUp(self):
        """ check file exists """
        if not os.path.exists(self.fname):
            raise Exception("You need " + self.fname + "for this test")
    def testcase(self):
        """ check we can read it"""
        obj = openimage(self.fname)
        obj2 = adscimage()
        obj2.read(self.fname)
        self.assertEqual(obj.data[10, 10], obj2.data[10, 10])
        self.assertEqual( type(obj), type(obj2) )
        # etc

class testadscgz(testadsc):
    """openimage opening adsc gzip"""
    fname = os.path.join("testimages","mb_LP_1_001.img.gz")

class testadscbz2(testadsc):
    """openimage opening adsc bzip"""
    fname = os.path.join("testimages","mb_LP_1_001.img.bz2")




from fabio.OXDimage import OXDimage

class testOXD(unittest.TestCase):
    """openimage opening adsc"""
    fname = os.path.join("testimages","b191_1_9_1.img")
    def setUp(self):
        """ check file exists """
        if not os.path.exists(self.fname):
            raise Exception("You need " + self.fname + "for this test")
    def testcase(self):
        """ check we can read it"""
        obj = openimage(self.fname)
        obj2 = OXDimage()
        obj2.read(self.fname)
        self.assertEqual(obj.data[10, 10], obj2.data[10, 10])
        self.assertEqual( type(obj), type(obj2) )
        # etc


class testOXD(unittest.TestCase):
    """openimage opening adsc"""
    fname = os.path.join("testimages","b191_1_9_1_uncompressed.img")





if __name__ == "__main__":
    unittest.main()
                         
