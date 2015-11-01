#!/usr/bin/env python
import sys
print("Python %s %s" % (sys.version, tuple.__itemsize__ * 8))

try: import numpy
except: print("Numpy missing")
else: print("Numpy %s" % numpy.version.version)



try: import h5py
except Exception as error: print("h5py missing: %s" % error)
else: print("h5py %s" % h5py.version.version)

try: import Cython
except: print("Cython missing")
else: print("Cython %s" % Cython.__version__)

try: import fabio
except:
    print("FabIO missing, using built version")
    """Adapter for utilstest from pyFAI.test"""
    import os
    home = os.path.abspath(__file__)
    sys.path.insert(0, home)
    from test.utilstest import *
else:
    print("FabIO %s" % fabio.version)
    sys.path.append("sandbox")


import logging
if "-v" in sys.argv:
    logging.root.setLevel(logging.INFO)
if "-d" in sys.argv:
    logging.root.setLevel(logging.DEBUG)

fabio.tests()
