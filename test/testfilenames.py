

import unittest

import fabio

cases = [
    ( 1,     'edf', "data0001.edf" ),
    ( 10001, 'edf', "data10001.edf"),
    ( 10001, 'edf', "data10001.edf.gz"),
    ( 10001, 'edf', "data10001.edf.bz2"),
    ( 2,     'marccd', "data0002.mccd" ),
    ( 12345, 'marccd', "data12345.mccd"),
    ( 10001, 'marccd', "data10001.mccd.gz"),
    ( 10001, 'marccd', "data10001.mccd.bz2"),
    ( 3,     'tif', "data0003.tif" ),
    ( 4,     'tif', "data0004.tiff" ),
    ( 99,    'bruker',"sucrose101.0099")
    ]

class testfilenames(unittest.TestCase):
    def test_many_cases(self):
        for num,typ,name in cases:
            fnum,ftyp = fabio.deconstruct_filename(name)
            self.assertEqual(num,fnum)
            self.assertEqual(ftyp,typ)
                    

if __name__ == "__main__":
    unittest.main()
        
        
