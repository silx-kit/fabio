#!/usr/bin/env python
import sys

import numpy

print(f"Python {tuple.__itemsize__ * 8} bits")
print(f"       maxsize: {sys.maxsize}\t maxunicode: {sys.maxunicode}")
print(sys.version)
try:
    from distutils.sysconfig import get_config_vars
except ImportError:
    from sysconfig import get_config_vars
print("Config "+" ".join(get_config_vars("CONFIG_ARGS")))
print()
print(f"Numpy {numpy.version.version}")
print(f"      include {numpy.get_include()}")
print(f"      options {numpy.get_printoptions()}")
