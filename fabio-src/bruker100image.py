#!/usr/bin/env python
# coding: utf-8


"""

Authors: Henning O. Sorensen & Erik Knudsen
         Center for Fundamental Research: Metal Structures in Four Dimensions
         Risoe National Laboratory
         Frederiksborgvej 399
         DK-4000 Roskilde
         email:erik.knudsen@risoe.dk


         Jérôme Kieffer, ESRF, Grenoble, France

"""
# get ready for python3
from __future__ import absolute_import, print_function, with_statement, division
__authors__ = ["Henning O. Sorensen" , "Erik Knudsen", "Jon Wright", "Jérôme Kieffer"]
__date__ = "19/03/2015"
__status__ = "production"
__copyright__ = "2007-2009 Risoe National Laboratory; 2015 ESRF"
__licence__ = "GPL"

import numpy
import math
import logging
logger = logging.getLogger("bruker100image")
try:
    from PIL import Image
except ImportError:
    logger.warning("PIL is not installed ... trying to do without")
    Image = None

from .brukerimage import brukerimage
from .readbytestream import readbytestream

class bruker100image(brukerimage):
    def __init__(self, data=None , header=None):
        brukerimage.__init__(self, data, header)
        self.version = 100

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
        with self._open(fname, "rb") as infile:
            try:
                self._readheader(infile)
            except:
                raise
            rows = self.dim1
            cols = self.dim2
            npixelb = int(self.header['NPIXELB'][0])
            # you had to read the Bruker docs to know this!

            # We are now at the start of the image - assuming bruker._readheader worked
            # Get image block size from NPIXELB.
            # The total size is nbytes * nrows * ncolumns.
            self.data = readbytestream(infile, infile.tell(), rows, cols, npixelb,
                                        datatype="int", signed='n', swap='n')


            # now process the overflows

            for k, nover in enumerate(self.header['NOVERFL'].split()):
                if k == 0:
                    # read the set of "underflow pixels" - these will be completely disregarded for now
                    continue
                nov = int(nover)
                if nov <= 0:
                    continue
                bpp = 1 << k  # (2 ** k)
                datatype = self.bpp_to_numpy[bpp]
                # upgrade data type
                self.data = self.data.astype(datatype)

                # pad nov*bpp to a multiple of 16 bytes
                nbytes = (nov * bpp + 15) & ~(15)

                # Multiple of 16 just above
                data_str = infile.read(nbytes)

                ar = numpy.fromstring(data_str[:nov * bpp], datatype)

                # insert the the overflow pixels in the image array:
                lim = (1 << (8 * k)) - 1
                # generate an array comprising of the indices into data.ravel()
                # where its value equals lim.
                flat = self.data.ravel()
                mask = numpy.where(flat == lim)[0]
                # now put values from ar into those indices
                flat.put(mask, ar)
                logger.debug("%s bytes read + %d bytes padding" % (nov * bpp, nbytes - nov * bpp))
#         infile.close()

        self.resetvals()
        return self

    def write(self, fname):
        """
        """
        raise NotImplementedError
        #TODO: make a writer !!!

if __name__ == '__main__':
    import sys, time
    I = bruker100image()
    b = time.clock()
    while (sys.argv[1:]):
        I.read(sys.argv[1])
        r = I.toPIL16()
        I.rebin(2, 2)
        print(sys.argv[1] + (": max=%d, min=%d, mean=%.2e, stddev=%.2e") % (
            I.getmax(), I.getmin(), I.getmean(), I.getstddev()))
        print('integrated intensity (%d %d %d %d) =%.3f' % (
            10, 20, 20, 40, I.integrate_area((10, 20, 20, 40))))
        sys.argv[1:] = sys.argv[2:]
    e = time.clock()
    print (e - b)
