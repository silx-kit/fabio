#!/usr/bin/env python
"""

Authors: Henning O. Sorensen & Erik Knudsen
         Center for Fundamental Research: Metal Structures in Four Dimensions
         Risoe National Laboratory
         Frederiksborgvej 399
         DK-4000 Roskilde
         email:erik.knudsen@risoe.dk

Based on: openbruker,readbruker, readbrukerheader functions in the opendata
         module of ImageD11 written by Jon Wright, ESRF, Grenoble, France

"""

import numpy, logging
logger = logging.getLogger("brukerimage")
from fabioimage import fabioimage
from readbytestream import readbytestream


class brukerimage(fabioimage):
    """
    Read and eventually write ID11 bruker (eg smart6500) images
    """

    # needed if you feel like writing - see ImageD11/scripts/edf2bruker.py

    __headerstring__ = ""


    def _readheader(self, infile):
        """
        the bruker format uses 80 char lines in key : value format
        In the fisrt 512*5 bytes of the header there should be a 
        HDRBLKS key, whose value denotes how many 512 byte blocks 
        are in the total header. The header is always n*5*512 bytes,
        otherwise it wont contain whole key: value pairs
        """
        lump = infile.read(512 * 5)
        self.__headerstring__ += lump
        i = 80
        self.header = {}
        while i < 512 * 5:
            if lump[i - 80: i].find(":") > 0:
                key, val = lump[i - 80: i].split(":", 1)
                key = key.strip()         # remove the whitespace (why?)
                val = val.strip()
                if self.header.has_key(key):
                    # append lines if key already there
                    self.header[key] = self.header[key] + '\n' + val
                else:
                    self.header[key] = val
                    self.header_keys.append(key)
            i = i + 80                  # next 80 characters
        # we must have read this in the first 512 bytes.
        nhdrblks = int(self.header['HDRBLKS'])
        # Now read in the rest of the header blocks, appending 
        rest = infile.read(512 * (nhdrblks - 5))
        self.__headerstring__ += rest
        lump = lump[i - 80: 512] + rest
        i = 80
        j = 512 * nhdrblks
        while i < j :
            if lump[i - 80: i].find(":") > 0: # as for first 512 bytes of header
                key, val = lump[i - 80: i].split(":", 1)
                key = key.strip()
                val = val.strip()
                if self.header.has_key(key):
                    self.header[key] = self.header[key] + '\n' + val
                else:
                    self.header[key] = val
                    self.header_keys.append(key)
            i = i + 80
        # make a (new) header item called "datastart"
        self.header['datastart'] = infile.tell()
        #set the image dimensions
        self.dim1 = int(self.header['NROWS'])
        self.dim2 = int(self.header['NCOLS'])

    def read(self, fname, frame=None):
        """
        Read in and unpack the pixels (including overflow table
        """
        infile = self._open(fname, "rb")
        try:
            self._readheader(infile)
        except:
            raise

        rows = self.dim1
        cols = self.dim2

        try:
            # you had to read the Bruker docs to know this!
            npixelb = int(self.header['NPIXELB'])
        except:
            errmsg = "length " + str(len(self.header['NPIXELB'])) + "\n"
            for byt in self.header['NPIXELB']:
                errmsg += "char: " + str(byt) + " " + str(ord(byt)) + "\n"
            logger.warning(errmsg)
            raise

        self.data = readbytestream(infile, infile.tell(),
                                   rows, cols, npixelb,
                                   datatype="int",
                                   signed='n',
                                   swap='n')

        #handle overflows
        nov = int(self.header['NOVERFL'])
        if nov > 0:   # Read in the overflows
            # need at least int32 sized data I guess - can reach 2^21
            self.data = self.data.astype(numpy.uint32)
            # 16 character overflows:
            #      9 characters of intensity
            #      7 character position
            for i in range(nov):
                ovfl = infile.read(16)
                intensity = int(ovfl[0: 9])
                position = int(ovfl[9: 16])
                # relies on python style modulo being always +
                row = position % rows
                # relies on truncation down
                col = position / rows
                #print "Overflow ", r, c, intensity, position,\
                #    self.data[r,c],self.data[c,r]
                self.data[col, row] = intensity
        infile.close()

        self.resetvals()
        self.pilimage = None
        return self


    def write(self, fname):
        """
        Writes the image as EDF
        FIXME - this should call edfimage.write if that is wanted?
        eg:     obj = edfimage(data = self.data, header = self.header)
                obj.write(fname)
                or maybe something like: edfimage.write(self, fname)
        """
        logger.warning("***warning***: call to unifinished " + \
                "brukerimage.write. This will write the file" + \
                            fname + "as an edf-file")


        outfile = self._open(fname, "wb")
        outfile.write('{\n')
        i = 4
        for k in self.header_keys:
            out = (("%s = %s;\n") % (k, self.header[k]))
            i = i + len(out)
            outfile.write(out)
        out = (4096 - i) * ' '
        outfile.write(out)
        outfile.write('}\n')
        # Assumes a short-circuiting if / or ...
        if not self.header.has_key("ByteOrder") or \
               self.header["ByteOrder"] == "LowByteFirst":
            outfile.write(self.data.astype(numpy.uint16).tostring())
        else:
            outfile.write(self.data.byteswap().astype(
                    numpy.uint16).tostring())
        outfile.close()

    def write2(self, fname):
        """ FIXME: what is this? """
        pass



def test():
    """ a testcase """
    import sys, time
    img = brukerimage()
    start = time.clock()
    for filename in sys.argv[1:]:
        img.read(filename)
        res = img.toPIL16()
        img.rebin(2, 2)
        print filename + (": max=%d, min=%d, mean=%.2e, stddev=%.2e") % (
            img.getmax(), img.getmin(), img.getmean(), img.getstddev())
        print 'integrated intensity (%d %d %d %d) =%.3f' % (
            10, 20, 20, 40, img.integrate_area((10, 20, 20, 40)))
    end = time.clock()
    print (end - start)



if __name__ == '__main__':
    test()


