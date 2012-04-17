#!/usr/bin/env python
#coding: utf8
"""

Authors: Henning O. Sorensen & Erik Knudsen
         Center for Fundamental Research: Metal Structures in Four Dimensions
         Risoe National Laboratory
         Frederiksborgvej 399
         DK-4000 Roskilde
         email:erik.knudsen@risoe.dk

+ mods for fabio by JPW

"""

import numpy, logging
from fabioimage import fabioimage
logger = logging.getLogger("adscimage")

class adscimage(fabioimage):
    """ Read an image in ADSC format (quite similar to edf?) """
    def __init__(self, *args, **kwargs):
        fabioimage.__init__(self, *args, **kwargs)

    def read(self, fname, frame=None):
        """ read in the file """
        infile = self._open(fname, "rb")
        try:
            self._readheader(infile)
        except:
            raise Exception("Error processing adsc header")
        # banned by bzip/gzip???
        try:
            infile.seek(int(self.header['HEADER_BYTES']), 0)
        except TypeError:
            # Gzipped does not allow a seek and read header is not
            # promising to stop in the right place
            infile.close()
            infile = self._open(fname, "rb")
            infile.read(int(self.header['HEADER_BYTES']))
        binary = infile.read()
        infile.close()

        #now read the data into the array
        self.dim1 = int(self.header['SIZE1'])
        self.dim2 = int(self.header['SIZE2'])
        if 'little' in self.header['BYTE_ORDER']:
            try:
                self.data = numpy.reshape(
                    numpy.fromstring(binary, numpy.uint16),
                    (self.dim2, self.dim1))
            except ValueError:
                raise IOError, 'Size spec in ADSC-header does not match ' + \
                    'size of image data field'
            self.bytecode = numpy.uint16
            logger.info("adscimage read in using low byte first (x386-order)")
        else:
            try:
                self.data = numpy.reshape(
                    numpy.fromstring(binary, numpy.uint16),
                    (self.dim2, self.dim1)).byteswap()
            except ValueError:
                raise IOError, 'Size spec in ADSC-header does not match ' + \
                    'size of image data field'
            self.bytecode = numpy.uint16
            logger.info('adscimage using high byte first (network order)')
        self.resetvals()
        return self


    def _readheader(self, infile):
        """ read an adsc header """
        line = infile.readline()
        bytesread = len(line)
        while '}' not in line:
            if '=' in line:
                (key, val) = line.split('=')
                self.header_keys.append(key.strip())
                self.header[key.strip()] = val.strip(' ;\n')
            line = infile.readline()
            bytesread = bytesread + len(line)


    def write(self, fname):
        """
        Write adsc format
        """
        out = '{\n'
        for key in self.header_keys:
            out += "%s = %s;\n" % (key, self.header[key])
        # FIXME ??? - made padding match header bytes keyword            
        #        the cbflib example image has exactly 512...
        if self.header.has_key("HEADER_BYTES"):
            pad = int(self.header["HEADER_BYTES"]) - len(out) - 2
        else:
            # integer division
            # 1234567890123456789012
            # HEADER_BYTES = 1234;\n
            hsize = ((len(out) + 23) / 512 + 1) * 512
            out += "HEADER_BYTES=%d;\n" % (hsize)
            pad = hsize - len(out) - 2
        out += pad * ' ' + "}\n"
        assert len(out) % 512 == 0 , "Header is not multiple of 512"
        outf = open(fname, "wb")
        outf.write(out)
        # it says "unsigned_short" ? ... jpw example has:
        # BYTE_ORDER=big_endian;
        # TYPE=unsigned_short;
        if "little" in self.header["BYTE_ORDER"]:
            outf.write(self.data.astype(numpy.uint16).tostring())
        else:
            outf.write(self.data.byteswap().astype(
                    numpy.uint16).tostring())
        outf.close()


def test():
    """ testcase """
    import sys, time
    img = adscimage()
    begin = time.clock()
    while (sys.argv[1:]):
        img.read(sys.argv[1])
#        rim = img.toPIL16()
        img.rebin(2, 2)
        img.write('jegErEnFil0000.img')
        print sys.argv[1] + ": max=%d, min=%d, mean=%.2e, stddev=%.2e" % (\
              img.getmax(), img.getmin(), img.getmean(), img.getstddev())
        print 'integrated intensity (%d %d %d %d) =%.3f' % (\
              10, 20, 20, 40, img.integrate_area((10, 20, 20, 40)))
        sys.argv[1:] = sys.argv[2:]
    end = time.clock()
    print end - begin


if __name__ == '__main__':
    test()
