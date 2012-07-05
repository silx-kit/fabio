import numpy
import math
import logging
logger = logging.getLogger("bruker100image")
try:
    import Image
except ImportError:
    logger.warning("PIL is not installed ... trying to do without")
    Image = None

from brukerimage import brukerimage
from readbytestream import readbytestream 

class bruker100image(brukerimage):


    def toPIL16(self, filename=None):
        if not Image:
            raise RuntimeError("PIL is not installed !!! ")

        if filename:
            self.read(filename)
        PILimage = Image.frombuffer("F",
                                        (self.dim1, self.dim2),
                                        self.data,
                                        "raw",
                                        "F;16", 0, -1)
        return PILimage

    def read(self, fname, frame=None):
        f = open(fname, "rb")
        try:
            self._readheader(f)
        except:
            raise

        rows = int(self.header['NROWS'])
        cols = int(self.header['NCOLS'])
        npixelb = int(self.header['NPIXELB'][0])
        # you had to read the Bruker docs to know this!

        # We are now at the start of the image - assuming 
        #   readbrukerheader worked
        # size = rows * cols * npixelb
        self.data = readbytestream(f, f.tell(), rows, cols, npixelb,
                                    datatype="int", signed='n', swap='n')

        noverfl = self.header['NOVERFL'].split() # now process the overflows
        #read the set of "underflow pixels" - these will be completely 
        # disregarded for now
        data = self.data
        k = 0

        while k < 2:#for the time being things - are done in 16 bits
            datatype = {'1' : numpy.uint8,
                        '2' : numpy.uint16,
                        '4' : numpy.uint32 }[("%d" % 2 ** k)]
            ar = numpy.array(numpy.fromstring(f.read(int(noverfl[k]) * (2 ** k)),
                                        datatype), numpy.uint16)
            #insert the the overflow pixels in the image array:
            #this is probably a memory intensive way of doing this - 
            # might be done in a more clever way
            lim = 2 ** (8 * k) - 1
            #generate an array comprising of the indices into data.ravel() 
            # where its value equals lim.
            M = numpy.compress(numpy.equal(data.ravel(), lim), numpy.arange(rows * cols))
            #now put values from ar into those indices
            numpy.put(data.ravel(), M, ar)
            padding = 16 * int(math.ceil(int(noverfl[k]) * (2 ** k) / 16.)) - \
                         int(noverfl[k]) * (2 ** k)
            f.seek(padding, 1)
            print noverfl[k] + " bytes read + %d bytes padding" % padding
            k = k + 1

        f.close()

        (self.dim1, self.dim2) = (rows, cols)
        print self.dim1, self.dim2
        self.resetvals()
        return self

if __name__ == '__main__':
    import sys, time
    I = bruker100image()
    b = time.clock()
    while (sys.argv[1:]):
        I.read(sys.argv[1])
        r = I.toPIL16()
        I.rebin(2, 2)
        print sys.argv[1] + (": max=%d, min=%d, mean=%.2e, stddev=%.2e") % (
            I.getmax(), I.getmin(), I.getmean(), I.getstddev())
        print 'integrated intensity (%d %d %d %d) =%.3f' % (
            10, 20, 20, 40, I.integrate_area((10, 20, 20, 40)))
        sys.argv[1:] = sys.argv[2:]
    e = time.clock()
    print (e - b)
