

import unittest, os


from fabio.openimage import openheader

NAMES = [
    os.path.join("testimages","F2K_Seb_Lyso0675_header_only.edf.gz"),
    os.path.join("testimages","F2K_Seb_Lyso0675_header_only.edf.bz2"),
    os.path.join("testimages","F2K_Seb_Lyso0675_header_only.edf")
    ]


class test1(unittest.TestCase):
    """openheader opening edf"""
    def testcase(self):
        """ check we can read it"""
        for name in NAMES:
            obj = openheader(name)
            self.assertEqual(obj.header["title"],
                             "ESPIA FRELON Image",
                             "Error on "+name)

if __name__ == "__main__":
    unittest.main()
                         
