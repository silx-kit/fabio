
"""
Benchmark the bz2 and gzip modules compared to their system counterparts
"""

import cProfile, os, time,random, gzip, bz2, struct, sys

try: 
    import pstats
except:
    print "Your package manager is probably teasing you"
    print "try sudo apt-get install python-profiler"
    import sys
    sys.exit()



print "Setting up"
npts = int(1e6)
data = [ random.random() for i in range(npts) ]
sdata = struct.pack( "d"*npts, *tuple(data) )
open("prof.dat","wb").write(sdata)

os.system("gzip -c prof.dat > prof.dat.gz")
os.system("bzip2 -c prof.dat > prof.dat.bz2")

print "Done setup"
sys.stdout.flush()
def tst(fobj, fname):
    fo = fobj(fname, "rb")
    ret = fo.read()
    return



print "Python gzip module"
start = time.time()
cProfile.run( "tst(gzip.GzipFile, 'prof.dat.gz')", "gzstats")
p = pstats.Stats("gzstats")
p.strip_dirs().sort_stats(-1).print_stats()
del p


print "Python bz2 module"
cProfile.run( "tst(bz2.BZ2File, 'prof.dat.bz2')", "bz2stats")
p = pstats.Stats("bz2stats")
p.strip_dirs().sort_stats(-1).print_stats()
del p

def tstsys(cmd):
    fo = os.popen(cmd,"rb")
    ret = fo.read()
    return

print "System gzip"
cProfile.run( "tstsys('gzip -cd prof.dat.gz')", "gzosstats")
p = pstats.Stats("gzosstats")
p.strip_dirs().sort_stats(-1).print_stats()
del p

print "System bz2"
cProfile.run( "tstsys('bzip2 -cd prof.dat.bz2')", "bz2osstats")
p = pstats.Stats("bz2osstats")
p.strip_dirs().sort_stats(-1).print_stats()
del p



import timeit

for s in ["ret = gzip.GzipFile('prof.dat.gz','rb').read()",
          "ret = os.popen('gzip -dc prof.dat.gz','rb').read()",
          "ret = os.popen('gzip -dc prof.dat.gz','rb',2**20).read()",
          "ret = bz2.BZ2File('prof.dat.bz2','rb').read()",
          "ret = os.popen('bzip2 -dc prof.dat.bz2','rb').read()",
          "ret = os.popen('bzip2 -dc prof.dat.bz2','rb',2**20).read()",
          ]:

    t = timeit.Timer(s,setup="import os, gzip, bz2")
    print s,":", t.timeit(10)/10

# Finally - shell version

print "Time shell bzip2"
sys.stdout.flush()
os.system("time bzip2 -cd prof.dat.bz2 > /dev/null")
print "Time shell gzip"
sys.stdout.flush()
os.system("time gzip -cd prof.dat.gz > /dev/null")
