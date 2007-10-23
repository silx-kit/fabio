
import unittest
import fabio

class test_next(unittest.TestCase):
    def test_next1(self):
        for name, next in [ [ "data0001.edf", "data0002.edf" ],
                [ "bob1.edf", "bob2.edf" ],
                [ "1.edf", "2.edf" ],
                [ "1.mar2300", "2.mar2300" ],
                ]:
            self.assertEqual( next, fabio.next_filename(name) )

class test_prev(unittest.TestCase):
    def test_prev1(self):
        for name, prev in [ [ "data0001.edf", "data0000.edf" ],
                [ "bob1.edf", "bob0.edf" ],
                [ "1.edf", "0.edf" ],
                [ "1.mar2300", "0.mar2300" ],
                ]:
            self.assertEqual( prev, fabio.previous_filename(name) )

class test_jump(unittest.TestCase):
    def test_jump1(self):
        for name, res, num in [ [ "data0001.edf", "data99993.edf" ,99993 ],
                [ "bob1.edf", "bob0.edf", 0 ],
                [ "1.edf", "123456.edf" , 123456],
                [ "mydata001.mar2300.gz", "mydata003.mar2300.gz", 3 ],
                ]:
            self.assertEqual( res, fabio.jump_filename(name, num) )


if __name__=="__main__":
    unittest.main()
