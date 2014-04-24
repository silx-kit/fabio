#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# Unit tests

# builds on stuff from ImageD11.test.testpeaksearch
"""
import unittest, sys, os, logging
logger = logging.getLogger("testopenimage")
force_build = False

for opts in sys.argv[:]:
    if opts in ["-d", "--debug"]:
        logging.basicConfig(level=logging.DEBUG)
        sys.argv.pop(sys.argv.index(opts))
    elif opts in ["-i", "--info"]:
        logging.basicConfig(level=logging.INFO)
        sys.argv.pop(sys.argv.index(opts))
    elif opts in ["-f", "--force"]:
        force_build = True
        sys.argv.pop(sys.argv.index(opts))
try:
    logger.debug("Tests loaded from file: %s" % __file__)
except:
    __file__ = os.getcwd()

from utilstest import UtilsTest
if force_build:
    UtilsTest.forceBuild()
import fabio

from utilstest import UtilsTest
from fabio.openimage import openimage
from fabio.edfimage import edfimage
from fabio.marccdimage import marccdimage
from fabio.fit2dmaskimage import fit2dmaskimage
from fabio.OXDimage import OXDimage
from fabio.brukerimage import brukerimage
from fabio.adscimage import adscimage

class testopenedf(unittest.TestCase):
    """openimage opening edf"""
    fname = "F2K_Seb_Lyso0675.edf.bz2"
    def setUp(self):
        self.fname = UtilsTest.getimage(self.__class__.fname)

    def testcase(self):
        """ check we can read EDF image with openimage"""
        obj = openimage(self.fname)
        obj2 = edfimage()
        obj2.read(self.fname)
        self.assertEqual(obj.data[10, 10], obj2.data[10, 10])
        self.assertEqual(type(obj), type(obj2))
        self.assertEqual(abs(obj.data.astype(int) - obj2.data.astype(int)).sum(), 0)

        # etc

class testedfgz(testopenedf):
    """openimage opening edf gzip"""
    fname = "F2K_Seb_Lyso0675.edf.gz"


class testedfbz2(testopenedf):
    """openimage opening edf bzip"""
    fname = "F2K_Seb_Lyso0675.edf.bz2"



class testopenmccd(unittest.TestCase):
    """openimage opening mccd"""
    fname = "somedata_0001.mccd"
    def setUp(self):
        self.fname = UtilsTest.getimage(self.__class__.fname)
    def testcase(self):
        """ check we can read it"""
        obj = openimage(self.fname)
        obj2 = marccdimage()
        obj2.read(self.fname)
        self.assertEqual(obj.data[10, 10], obj2.data[10, 10])
        self.assertEqual(type(obj), type(obj2))
        self.assertEqual(abs(obj.data.astype(int) - obj2.data.astype(int)).sum(), 0)

        # etc

class testmccdgz(testopenmccd):
    """openimage opening mccd gzip"""
    fname = "somedata_0001.mccd.gz"


class testmccdbz2(testopenmccd):
    """openimage opening mccd bzip"""
    fname = "somedata_0001.mccd.bz2"





class testmask(unittest.TestCase):
    """openimage opening mccd"""
    fname = "face.msk"
    def setUp(self):
        """ check file exists """
        self.fname = UtilsTest.getimage(self.__class__.fname)

    def testcase(self):
        """ check we can read Fit2D mask with openimage"""
        obj = openimage(self.fname)
        obj2 = fit2dmaskimage()
        obj2.read(self.fname)
        self.assertEqual(obj.data[10, 10], obj2.data[10, 10])
        self.assertEqual(type(obj), type(obj2))
        self.assertEqual(abs(obj.data.astype(int) - obj2.data.astype(int)).sum(), 0)
        self.assertEqual(abs(obj.data.astype(int) - obj2.data.astype(int)).sum(), 0)
        # etc

class testmaskgz(testmask):
    """openimage opening mccd gzip"""
    fname = "face.msk.gz"

class testmaskbz2(testmask):
    """openimage opening mccd bzip"""
    fname = "face.msk.bz2"





class testbruker(unittest.TestCase):
    """openimage opening bruker"""
    fname = "Cr8F8140k103.0026"
    def setUp(self):
        self.fname = UtilsTest.getimage(self.__class__.fname)
    def testcase(self):
        """ check we can read it"""
        obj = openimage(self.fname)
        obj2 = brukerimage()
        obj2.read(self.fname)
        self.assertEqual(obj.data[10, 10], obj2.data[10, 10])
        self.assertEqual(type(obj), type(obj2))
        self.assertEqual(abs(obj.data.astype(int) - obj2.data.astype(int)).sum(), 0)
        # etc

class testbrukergz(testbruker):
    """openimage opening bruker gzip"""
    fname = "Cr8F8140k103.0026.gz"

class testbrukerbz2(testbruker):
    """openimage opening bruker bzip"""
    fname = "Cr8F8140k103.0026.bz2"




class testadsc(unittest.TestCase):
    """openimage opening adsc"""
    fname = os.path.join("testimages", "mb_LP_1_001.img")
    def setUp(self):
        self.fname = UtilsTest.getimage("mb_LP_1_001.img.bz2")
    def testcase(self):
        """ check we can read it"""
        obj = openimage(self.fname)
        obj2 = adscimage()
        obj2.read(self.fname)
        self.assertEqual(obj.data[10, 10], obj2.data[10, 10])
        self.assertEqual(type(obj), type(obj2))
        self.assertEqual(abs(obj.data.astype(int) - obj2.data.astype(int)).sum(), 0)
        # etc

class testadscgz(testadsc):
    """openimage opening adsc gzip"""
    fname = os.path.join("testimages", "mb_LP_1_001.img.gz")

class testadscbz2(testadsc):
    """openimage opening adsc bzip"""
    fname = os.path.join("testimages", "mb_LP_1_001.img.bz2")





class testOXD(unittest.TestCase):
    """openimage opening adsc"""
    fname = "b191_1_9_1.img.bz2"
    def setUp(self):
        self.fname = UtilsTest.getimage(self.__class__.fname)[:-4]
    def testcase(self):
        """ check we can read OXD images with openimage"""
        obj = openimage(self.fname)
        obj2 = OXDimage()
        obj2.read(self.fname)
        self.assertEqual(obj.data[10, 10], obj2.data[10, 10])
        self.assertEqual(type(obj), type(obj2))
        self.assertEqual(abs(obj.data.astype(int) - obj2.data.astype(int)).sum(), 0)
        # etc


class testOXDUNC(testOXD):
    """openimage opening oxd"""
    fname = "b191_1_9_1_uncompressed.img.bz2"
    def setUp(self):
        self.fname = UtilsTest.getimage(self.__class__.fname)[:-4]


def test_suite_all_openimage():
    testSuite = unittest.TestSuite()
    testSuite.addTest(testedfbz2("testcase"))
    testSuite.addTest(testopenedf("testcase"))
    testSuite.addTest(testedfgz("testcase"))

    testSuite.addTest(testmccdbz2("testcase"))
    testSuite.addTest(testopenmccd("testcase"))
    testSuite.addTest(testmccdgz("testcase"))

    testSuite.addTest(testmaskbz2("testcase"))
    testSuite.addTest(testmask("testcase"))
    testSuite.addTest(testmaskgz("testcase"))

    testSuite.addTest(testbrukerbz2("testcase"))
    testSuite.addTest(testbruker("testcase"))
    testSuite.addTest(testbrukergz("testcase"))

    testSuite.addTest(testadscbz2("testcase"))
    testSuite.addTest(testadsc("testcase"))
    testSuite.addTest(testadscgz("testcase"))

    testSuite.addTest(testOXD("testcase"))
    testSuite.addTest(testOXDUNC("testcase"))

    return testSuite

if __name__ == '__main__':
    mysuite = test_suite_all_openimage()
    runner = unittest.TextTestRunner()
    runner.run(mysuite)
