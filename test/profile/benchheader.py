

import timeit, os, sys
sys.path.insert(0, os.path.abspath("../build/lib.linux-x86_64-2.6"))

junk = [".svn", "testfile", "testfile.bz2", "testfile.gz"]

#for fname in :
#    if fname.find("") == -1:
#        images.append(fname)
images = [os.path.join("testimages", i) for i in os.listdir("testimages") if (i not in junk) ]
images.sort()
for im in images:
    s = "ret = fabio.openimage.openheader(r\"%s\")" % (im)
    t = timeit.Timer(s,
            setup="import fabio.openimage")
    print "%10.6f" % (t.timeit(10) / 10.0), im




