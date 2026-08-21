#!/usr/bin/env python

"""
Test import all submodules
"""

import logging
import os
import unittest

logger = logging.getLogger(__name__)


class TestImport(unittest.TestCase):
    def test_import_all(self):
        import fabio
        skip_without_qt = {
            "fabio.app.viewer",
            "fabio.qt.dialogs",
            "fabio.qt.matplotlib",
        }
        with_qt = os.environ.get("WITH_QT_TEST", "True").lower() not in ("0", "false", "no")
    
        base = os.path.split(fabio.__path__[0])[0] + "/"
        for root, dirs, files in os.walk(fabio.__path__[0]):
            for f in files:
                if f.endswith(".py"):
                    module = os.path.join(root, f[:-3])[len(base):].replace(os.sep, ".")
                    if not with_qt and module in skip_without_qt:
                        continue
                    __import__(module)

def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(TestImport))
    return testsuite


if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite())
