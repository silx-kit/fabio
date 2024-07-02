#!/usr/bin/env python

"""
Test import all submodules
"""

import os
import unittest
import logging

logger = logging.getLogger(__name__)



class TestImport(unittest.TestCase):
    def test_import_all(self):
        import fabio
        base = os.path.split(fabio.__path__[0])[0]+"/"
        for root, dirs, files in os.walk(fabio.__path__[0]):
            for f in files:
                if f.endswith(".py"):
                    module = os.path.join(root, f[:-3])[len(base):].replace(os.sep,".")
                    __import__(module)


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestImport))
    return testsuite


if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite())
