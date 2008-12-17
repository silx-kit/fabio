

import glob, os, fabio.openimage, libtiff3ctypes, traceback

fl = ['fit2d.tif']
fl += glob.glob( os.path.join("libtiffpic","*.tif"))
fl += glob.glob( os.path.join("libtiffpic","depth","*.tif"))

passed=0
failed=0

# Try with fabio
for f in fl:
    try:
        im = fabio.openimage.openimage(f)
        l = len(im.data.flat)
        print "Passed for",f, im.data.shape, im.data.flat[l/2]
        passed += 1
    except:
        print "Failed for",f
        failed += 1

print passed, failed, passed+failed
passed=0
failed=0
print "******************************"

# Now with libtiff
for f in fl:
    try:
        tags, data = libtiff3ctypes.GetTiffTagsAndData(f)
        l = len(data)
        print "Passed for",f, l, data[l/2]
        passed += 1
    except:
        print "Failed for",f
        failed += 1
        traceback.print_exc()



print passed, failed, passed+failed
