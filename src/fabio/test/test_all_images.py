
"""
Check we can read all the test images
"""

import glob
import os
import time
import fabio.openimage
import gzip
import bz2
import pstats
import sys

try:
    import cProfile
except ImportError:
    import profile as cProfile

times = {}
images = []

for fname in glob.glob(os.path.join("testimages", "*")):
    if fname.find("header_only") == -1:
        images.append(fname)

images.sort()


def shellbench(cmd, imname):
    """
    The shell appears to be lying about it's performance. It claims
    zero time to gunzip a file when it actually takes 200 ms. This is
    cheating via a cache I suspect. We shall try to avoid this problem
    """
    if sys.platform != "win32":
        os.system("touch " + imname)
    astart = time.time()
    dummy_file = os.popen(cmd + " " + imname, "rb").read()
    return time.time() - astart


print("I/O 1  : Time to read the image")
print("I/O 2  : Time to read the image (repeat")
print("Fabio  : Time for fabio to read the image")
print("Shell  : Time for shell to do decompression")
print("Python : Time for python to do decompression\n")

print("I/O 1  I/O 2  Fabio  Shell  Python   Size/MB")
for im in images:
    # Network/disk io time first
    start = time.clock()
    the_file = open(im, "rb").read()
    times[im] = [time.clock() - start]
    start = time.clock()
    # Network/disk should be cached
    the_file = open(im, "rb").read()
    times[im].append(time.clock() - start)
    start = time.clock()
    try:
        fim = fabio.openimage.openimage(im)
    except KeyboardInterrupt:
        raise
    except Exception:
        print("Problem with image %s" % im)
        continue
    times[im].append(time.clock() - start)
    nt = 3
    ns = 2
    # Now check for a fabio slowdown effect
    if im[-3:] == '.gz':
        times[im].append(shellbench("gzip -cd ", im))
        nt += 1
        ns -= 1
        start = time.clock()
        the_file = gzip.GzipFile(im, "rb").read()
        times[im].append(time.clock() - start)
        nt += 1
        ns -= 1
    if im[-4:] == '.bz2':
        times[im].append(shellbench("bzip2 -cd ", im))
        nt += 1
        ns -= 1
        start = time.clock()
        the_file = bz2.BZ2File(im, "rb").read()
        times[im].append(time.clock() - start)
        nt += 1
        ns -= 1
    # Speed ratings in megabytes per second (for fabio)
    MB = len(the_file) / 1024.0 / 1024.0
    try:
        print(("%.4f " * nt + " " * 7 * ns) % tuple(times[im]), "%8.3f" % (MB), im)
    except Exception:
        print(times[im], MB, im)
        raise

    cProfile.run("fabio.openimage.openimage(im)", "stats")
    p = pstats.Stats("stats")
    # Hack around python2.4
    s = sys.stdout
    sys.stdout = open("profile.txt", "a")
    p.strip_dirs().sort_stats(-1).print_stats()
    sys.stdout = s
