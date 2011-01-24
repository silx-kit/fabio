#!/usr/bin/python



import os, subprocess, sys, distutils.util

def lintit(infile, outfile):
    print ("Updating %s" % outfile)
    process = subprocess.Popen(["pylint", infile], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    rc = process.wait()
    result = process.stdout.read()
    if len(result) > 0:
        open(outfile, "wb").write(result)
    else:
        print ("Error in running pylint on %s" % infile)

arch = "lib.%s-%i.%i" % (distutils.util.get_platform(), sys.version_info[0], sys.version_info[1])
installDir = os.path.abspath(os.path.join("..", "build", arch, "fabio"))
testDir = os.path.abspath(os.path.join("..", "test"))

sys.path.append(installDir)
files = [ os.path.join(installDir, i) for i in os.listdir(installDir) if i.endswith(".py") ] + \
        [ os.path.join(testDir, i) for i in os.listdir(testDir) if i.endswith(".py") ]

for f in files:
#    print f
    outf = os.path.split(f)[-1] + ".lint"
    if not os.path.exists(outf) :
        lintit(f, outf)
    elif os.stat(f).st_mtime > os.stat(outf).st_mtime:
        lintit(f, outf)
    else:
        print ("Not updating %s" % outf)
#    lintit(f, outf)
