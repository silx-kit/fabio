

import timeit, glob, os, sys
sys.path.insert(0, os.path.abspath("../build/lib.linux-x86_64-2.6"))
images = []
for fname in glob.glob(os.path.join("testimages", "*")):
    if fname.find("header_only") == -1:
        images.append(fname)
images.sort()
for im in images:
    s = "ret = fabio.openimage.openheader(r\"%s\")" % (im)
    t = timeit.Timer(s,
            setup="import fabio.openimage")
    print "%10.6f" % (t.timeit(10) / 10.0), im




