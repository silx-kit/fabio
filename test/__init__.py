import unittest
import test_all
#print test_all.__file__
#print dir(test_all)
test_all_images = unittest.TestSuite()
test_all_images.addTest(test_all.test_suite_all())
runner = unittest.TextTestRunner()
runner.run(test_all_images)
