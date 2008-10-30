

import unittest, os
import fabio.openimage


class test_flat_binary(unittest.TestCase):

    filenames = [
        "not.a.file",
        "bad_news_1234",
        "empty_files_suck_1234.edf",
        "notRUBY_1234.dat"]
    
    def setUp(self):
        for filename in self.filenames:
            f = open(filename,"wb")
            # A 2048 by 2048 blank image
            f.write("\0x0"*2048*2048*2)
        f.close()
        
    def test_openimage(self):
        nfail = 0
        for filename in self.filenames:
            try:
                im = fabio.openimage.openimage( filename )
                if im.data.tostring() != "\0x0"*2048*2048*2:
                    nfail += 1
                else:
                    print "**** Passed", filename
            except:
                print "failed for",filename
                nfail += 1
        assert nfail == 0, str(nfail)+" failures out of "+str(len(self.filenames))        
    def tearDown(self):
        for filename in self.filenames:
            os.remove(filename)

if __name__=="__main__":
    unittest.main()
