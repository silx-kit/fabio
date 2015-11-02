#!/usr/bin/env python
import sys
import os
import logging

print("Python %s %s" % (sys.version, tuple.__itemsize__ * 8))

try:
    import numpy
except:
    print("Numpy missing")
else:
    print("Numpy %s" % numpy.version.version)



try:
    import h5py
except Exception as error: print("h5py missing: %s" % error)
else:
    print("h5py %s" % h5py.version.version)

try:
    import Cython
except:
    print("Cython missing")
else:
    print("Cython %s" % Cython.__version__)


try:
    from argparse import ArgumentParser
except ImportError:
    from fabio.third_party.argparse import ArgumentParser
parser = ArgumentParser(description='Run the tests.')

parser.add_argument("-i", "--insource",
                    action="store_true", dest="insource", default=False,
                    help="Use the build source and not the installed version")
parser.add_argument("-c", "--coverage", dest="coverage",
                    action="store_true", default=False,
                    help="report coverage of fabio code (requires 'coverage' module)")
parser.add_argument("-v", "--verbose",
                    action="count", dest="verbose",
                    help="increase verbosity")
options = parser.parse_args()
sys.argv = [sys.argv[0]]
if options.verbose == 1:
    logging.root.setLevel(logging.INFO)
    print("Set log level: INFO")
elif options.verbose > 1:
    logging.root.setLevel(logging.DEBUG)
    print("Set log level: DEBUG")

if not options.insource:
    try:
        import fabio
    except:
        print("FabIO missing, using built (i.e. not installed) version")
        options.insource = True
if options.insource:
    home = os.path.abspath(__file__)
    sys.path.insert(0, home)
    from test.utilstest import *
    import fabio

print("FabIO %s from %s" % (fabio.version, fabio.__path__))


if options.coverage:
    print("Running test-coverage")
    import coverage
    source = os.path.dirname(fabio.__file__)
    try:
        cov = coverage.Coverage(source=fabio.__path__, omit=["*test*", "*third_party*"])
    except AttributeError:
        cov = coverage.coverage(source=fabio.__path__, omit=["*test*", "*third_party*"])

    cov.start()

fabio.tests()

if options.coverage:
    cov.stop()
    cov.save()
    print(cov.report())

