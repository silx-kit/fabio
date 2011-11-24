
import unittest, sys, os, logging
logger = logging.getLogger("test_flat_binary")
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


class test_flat_binary(unittest.TestCase):

    filenames = [
        "not.a.file",
        "bad_news_1234",
        "empty_files_suck_1234.edf",
        "notRUBY_1234.dat"]

    def setUp(self):
        for filename in self.filenames:
            f = open(filename, "wb")
            # A 2048 by 2048 blank image
            f.write("\0x0" * 2048 * 2048 * 2)
        f.close()

    def NOtest_openimage(self):
        """
        test the opening of "junk" empty images ...
        JK: I wonder if this test makes sense !
        """
        nfail = 0
        for filename in self.filenames:
            try:
                im = fabio.open(filename)
                if im.data.tostring() != "\0x0" * 2048 * 2048 * 2:
                    nfail += 1
                else:
                    logger.info("**** Passed: %s" % filename)
            except:
                logger.warning("failed for: %s" % filename)
                nfail += 1
        self.assertEqual(nfail, 0, " %s failures out of %s" % (nfail, len(self.filenames)))

    def tearDown(self):
        for filename in self.filenames:
            os.remove(filename)

#def test_suite_all_flat():
#    testSuite = unittest.TestSuite()
#
#    testSuite.addTest(test_flat_binary("test_openimage"))
#    return testSuite

if __name__ == '__main__':
    mysuite = test_suite_all_flat()
    runner = unittest.TextTestRunner()
    runner.run(mysuite)
