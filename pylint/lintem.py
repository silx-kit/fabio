#!/usr/bin/python
# coding: utf-8
from __future__ import with_statement

__author__ = "Jerome Kieffer"
__email__ = "jerome.kieffer@esrf.fr"
__doc__ = "This runs pylint on all modules from fabio package"
__date__ = "20120416"
__status__ = "production"
__licence__ = "GPL"

import os, subprocess, sys, distutils.util
import numpy
import Image
from os.path import dirname
arch = "lib.%s-%i.%i" % (distutils.util.get_platform(), sys.version_info[0], sys.version_info[1])
pylint_dir = os.path.dirname(os.path.abspath(__file__))
fabio_root = os.path.dirname(pylint_dir)
installDir = os.path.abspath(os.path.join(fabio_root, "build", arch, "fabio"))
testDir = os.path.abspath(os.path.join(fabio_root, "test"))
sys.path.append(testDir)
import utilstest
#env = {"PYTHONPATH":":".join([installDir, testDir, dirname(dirname(numpy.__file__)), dirname(Image.__file__)])}
env = {"PYTHONPATH":installDir}
print env
def lintit(infile, outfile):
    print ("Updating %s" % outfile)
    process = subprocess.Popen(["pylint", infile], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    result, error = process.communicate()
    if len(result) > 0:
        with open(outfile, "wb") as lintfile:
            if len(error) > 0:
                lintfile.write(error + os.linesep)
            lintfile.write(result)
    else:
        print ("Error in running pylint on %s:%s%s" % (infile, os.linesep, error))

files = [ os.path.join(installDir, i) for i in os.listdir(installDir) if i.endswith(".py") ] + \
        [ os.path.join(testDir, i) for i in os.listdir(testDir) if i.endswith(".py") ]

for f in files:
    outf = os.path.join(pylint_dir, os.path.basename(f) + ".lint")
    if not os.path.exists(outf) :
        lintit(f, outf)
    elif os.stat(f).st_mtime > os.stat(outf).st_mtime:
        lintit(f, outf)
    else:
        print ("Not updating %s" % outf)
#    lintit(f, outf)
