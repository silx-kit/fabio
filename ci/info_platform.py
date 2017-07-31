#!/usr/bin/env python
import sys, numpy
print("Python %s bits" % (tuple.__itemsize__ * 8))
print("       maxsize: %s\t maxunicode: %s" % (sys.maxsize, sys.maxunicode))
print(sys.version)
try:
    from distutils.sysconfig import get_config_vars
except:
    from sysconfig import get_config_vars
print("Config "+" ".join(get_config_vars("CONFIG_ARGS")))
print()
print("Numpy %s" % numpy.version.version)
print("      include %s" % numpy.get_include())
print("      options %s" % numpy.get_printoptions())
