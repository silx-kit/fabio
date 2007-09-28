#!/usr/bin/python



import glob, os

def lintit(infile,outfile):
    print infile,outfile
    os.system("pylint %s > %s"%(infile,outfile))


files = glob.glob("../build/lib.linux-i686-2.5/fabio/*.py") + \
        glob.glob("../test/*.py")

for f in files:
    outf = os.path.split(f)[-1] + ".lint"
    if not os.path.exists(outf) :
        lintit(f,outf)
        continue
    if os.stat(f).st_mtime > os.stat(outf).st_mtime:
        lintit(f,outf)
        continue

