

import glob, os, time, fabio.openimage

images = glob.glob(os.path.join("testimages","*"))


for im in images:
    start = time.clock()
    try:
        fim = fabio.openimage.openimage(im)
    except:
        print "Problem with",im
        continue
        # raise
    print "\n%.5f %s"%(time.clock()-start, im)
    
        
    
