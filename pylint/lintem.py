#!/usr/bin/python



import glob, os

def lintit(infile,outfile):
    print infile,outfile
    os.system("pylint %s > %s"%(infile,outfile))


files = glob.glob("../src/*.py") + glob.glob("../test/*.py")

for f in files:
    outf = os.path.split(f)[-1] + ".lint"
    if not os.path.exists(outf) :
        lintit(f,outf)
        continue
    if os.stat(f).st_mtime > os.stat(outf).st_mtime:
        lintit(f,outf)
        continue

