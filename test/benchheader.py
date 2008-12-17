

import timeit, glob, os
images = []
for fname in glob.glob(os.path.join("testimages","*")):
    if fname.find("header_only") == -1:
        images.append(fname)
images.sort()
for im in images:
    s  = "ret = fabio.openimage.openheader(r\"%s\")" % ( im )
    t = timeit.Timer(s,
            setup = "import fabio.openimage")
    print "%10.6f" % (t.timeit(10)/10.0), im




