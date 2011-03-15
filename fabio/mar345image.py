#!/usr/bin/env python
"""

Authors: Henning O. Sorensen & Erik Knudsen
         Center for Fundamental Research: Metal Structures in Four Dimensions
         Risoe National Laboratory
         Frederiksborgvej 399
         DK-4000 Roskilde
         email:erik.knudsen@risoe.dk
          +
         Jon Wright, ESRF, France
"""

from fabioimage import fabioimage
import numpy, struct, string

class mar345image(fabioimage):
    _need_a_real_file = True
    def read(self, fname):
        """ Read a mar345 image"""
        self.filename = fname
        f = self._open(self.filename, "rb")
        self._readheader(f)

        try:
            import mar345_io
        except:
            print 'error importing the mar345_io backend - ' + \
                'generating empty 1x1 picture'
            f.close()
            self.dim1 = 1
            self.dim2 = 1
            self.bytecode = numpy.int #
            self.data = numpy.resize(numpy.array([0], numpy.int), [1, 1])
            return self

        if 'compressed' in self.header['Format']:
            self.data = mar345_io.unpack(f, self.dim1, self.dim2, self.numhigh)
        else:
            print "error: cannot handle these formats yet " + \
                "due to lack of documentation"
            return None
        self.bytecode = numpy.uint
        f.close()
        return self

    def _readheader(self, infile=None):
        """ Read a mar345 image header """
        # clip was not used anywhere - commented out
        # clip = '\x00'
        #using a couple of local variables inside this function
        f = infile
        h = {}

        #header is 4096 bytes long
        l = f.read(64)
        #the contents of the mar345 header is taken to be as
        # described in
        # http://www.mar-usa.com/support/downloads/mar345_formats.pdf
        #the first 64 bytes are 4-byte integers (but in the CBFlib
        # example image it seems to 128 bytes?)
        #first 4-byte integer is a marker to check endianness
        # TODO: turn this into a real check
        if (l[0:4] == '1234'):
            fs = 'I'
        # unsigned integer, was using unsigned long (64 bit?)
        fs = 'i'
        #image dimensions
        self.dim1 = self.dim2 = int(struct.unpack(fs, l[4:8])[0])
        #number of high intensity pixels
        self.numhigh = struct.unpack(fs, l[2 * 4 : (2 + 1) * 4])[0]
        h['NumHigh'] = self.numhigh
        #Image format
        i = struct.unpack(fs, l[3 * 4 : (3 + 1) * 4])[0]
        if i == 1:
            h['Format'] = 'compressed'
        elif i == 2:
            h['Format'] = 'spiral'
        else:
            h['Format'] = 'compressed'
            print "warning: image format could not be detetermined" + \
                "- assuming compressed mar345"
        #collection mode
        h['Mode'] = {0:'Dose', 1: 'Time'}[struct.unpack(fs, l[4 * 4:(4 + 1) * 4])[0]]
        #total number of pixels
        self.numpixels = struct.unpack(fs, l[5 * 4:(5 + 1) * 4])[0]
        h['NumPixels'] = str(self.numpixels)
        #pixel dimensions (length,height) in mm
        h['PixelLength'] = struct.unpack(fs, l[6 * 4:(6 + 1) * 4])[0] / 1000.0
        h['PixelHeight'] = struct.unpack(fs, l[7 * 4:(7 + 1) * 4])[0] / 1000.0
        #x-ray wavelength in AA
        h['Wavelength'] = struct.unpack(fs, l[8 * 4:(8 + 1) * 4])[0] / 1000000.0
        #used distance
        h['Distance'] = struct.unpack(fs, l[9 * 4:(9 + 1) * 4])[0] / 1000.0
        #starting and ending phi
        h['StartPhi'] = struct.unpack(fs, l[10 * 4:11 * 4])[0] / 1000.0
        h['EndPhi'] = struct.unpack(fs, l[11 * 4:12 * 4])[0] / 1000.0
        #starting and ending omega
        h['StartOmega'] = struct.unpack(fs, l[12 * 4:13 * 4])[0] / 1000.0
        h['EndOmega'] = struct.unpack(fs, l[13 * 4:14 * 4])[0] / 1000.0
        #Chi and Twotheta angles
        h['Chi'] = struct.unpack(fs, l[14 * 4:15 * 4])[0] / 1000.0
        h['TwoTheta'] = struct.unpack(fs, l[15 * 4:16 * 4])[0] / 1000.0

        #the rest of the header is ascii
        # TODO: validate these values against the binaries already read
        l = f.read(128)
        if not 'mar research' in l:
            print "warning: the string \"mar research\" should be in " + \
                "bytes 65-76 of the header but was not"
        l = string.strip(f.read(4096 - 128 - 64))
        for m in l.splitlines():
            if m == 'END OF HEADER': break
            n = m.split(' ', 1)
            if n[0] == '':
                continue
            if n[0] in ('PROGRAM', 'DATE', 'SCANNER', 'HIGH', 'MULTIPLIER',
                        'GAIN', 'WAVELENGTH', 'DISTANCE', 'RESOLUTION',
                        'CHI', 'TWOTHETA', 'MODE', 'TIME', 'GENERATOR',
                        'MONOCHROMATOR', 'REMARK'):
                h[n[0]] = n[1].strip()
                continue
            if n[0] in ('FORMAT'):
                (h['DIM'], h['FORMAT_TYPE'], h['NO_PIXELS']) = n[1].split()
                continue
            if n[0] in ('PIXEL', 'OFFSET', 'PHI', 'OMEGA', 'COUNTS',
                        'CENTER', 'INTENSITY', 'HISTOGRAM', 'COLLIMATOR'):
                n = m.split()
                h.update([(n[0] + '_' + n[j], n[j + 1]) for j in range(1, len(n), 2)])
                continue
        self.header = h
        return h

    def write(self):
        pass

