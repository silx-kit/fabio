#!/usr/bin/env python
import sys, numpy
print("Python %s bits" % (tuple.__itemsize__ * 8))
print("       maxsize: %s\t maxunicode: %s" % (sys.maxsize, sys.maxunicode))
print(sys.version)
try:
    from distutils.sysconfig import get_config_vars
except:
    from sysconfig import get_config_vars
for k, v in get_config_vars().items():
    print("\t%s: %s" % (k, v))

print("Numpy %s" % numpy.version.version)
print("      include %s" % numpy.get_include())
print("      options %s" % numpy.get_printoptions())
