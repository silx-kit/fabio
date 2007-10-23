

"""
Test cases for filename deconstruction
"""

import unittest

import fabio , os

CASES = [
    ( 1,     'edf', "data0001.edf" ),
    ( 10001, 'edf', "data10001.edf"),
    ( 10001, 'edf', "data10001.edf.gz"),
    ( 10001, 'edf', "data10001.edf.bz2"),
    ( 2,     'marccd', "data0002.mccd" ),
    ( 12345, 'marccd', "data12345.mccd"),
    ( 10001, 'marccd', "data10001.mccd.gz"),
    ( 10001, 'marccd', "data10001.mccd.bz2"),
    ( 123,   'marccd', "data123.mccd.gz"),
    ( 3,     'tif', "data0003.tif" ),
    ( 4,     'tif', "data0004.tiff" ),
    ( 12,    'bruker',"sucrose101.012.gz"),
    ( 99,    'bruker',"sucrose101.099"),
    ( 99,    'bruker',"sucrose101.0099"),
    ( 99,    'bruker',"sucrose101.0099.bz2"),
    ( 99,    'bruker',"sucrose101.0099.gz"),
    ( 2,     'fit2dmask', "fit2d.msk"),
    ( None,  'fit2dmask', "mymask.msk"),
    ( 670005, 'edf' , 'S82P670005.edf'),
    ( 670005, 'edf' , 'S82P670005.edf.gz'),
    ( 1     , 'adsc' , 'mb_LP_1_001.img' ),
    ( 2     , 'adsc' , 'mb_LP_1_002.img.gz' ),
    ( 3     , 'adsc' , 'mb_LP_1_003.img.bz2' ),
    ( 3     , 'adsc' , os.path.join("data", 'mb_LP_1_003.img.bz2' )),
    ]



class testfilenames(unittest.TestCase):
    """ check the name -> number, type conversions """
    def test_many_cases(self):
        """ loop over CASES """
        for num, typ, name in CASES:
            obj = fabio.deconstruct_filename(name)
            self.assertEqual(num, obj.num , name+" num="+str(num)+\
                                                 " != obj.num="+str(obj.num))
            self.assertEqual(typ, obj.format, name)
            self.assertEqual(name, obj.tostring() , name+" "+obj.tostring())

if __name__ == "__main__":
    unittest.main()
