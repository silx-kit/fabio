#!/usr/bin/env python
#coding: utf8 
from __future__ import with_statement
"""

Authors: Henning O. Sorensen & Erik Knudsen
         Center for Fundamental Research: Metal Structures in Four Dimensions
         Risoe National Laboratory
         Frederiksborgvej 399
         DK-4000 Roskilde
         email:erik.knudsen@risoe.dk
          +
         Jon Wright, Jerome Kieffer, Gael Goret ESRF, France
"""

from fabioimage import fabioimage
from __init__ import version
import numpy, struct, string, time
import logging
logger = logging.getLogger("mar345image")


class mar345image(fabioimage):
    _need_a_real_file = True
    def __init__(self, *args, **kwargs):
        fabioimage.__init__(self, *args, **kwargs)
        self.numhigh = None
        self.numpixels = None

    def read(self, fname, frame=None):
        """ Read a mar345 image"""
        self.filename = fname
        f = self._open(self.filename, "rb")
        self._readheader(f)

        try:
            import mar345_io #IGNORE:F0401
        except ImportError, error:
            logger.error('%s. importing the mar345_io backend: generate an empty 1x1 picture' % error)
            f.close()
            self.dim1 = 1
            self.dim2 = 1
            self.bytecode = numpy.int #
            self.data = numpy.resize(numpy.array([0], numpy.int), [1, 1])
            return self

        if 'compressed' in self.header['Format']:
            self.data = mar345_io.unpack(f, self.dim1, self.dim2, self.numhigh)
        else:
            logger.error("cannot handle these formats yet " + \
                "due to lack of documentation")
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
            logger.warning("image format could not be detetermined" + \
                "- assuming compressed mar345")
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
            logger.warning("the string \"mar research\" should be in " + \
                "bytes 65-76 of the header but was not")
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

    def write(self, fname):
        with  self._open(fname, mode="wb") as outfile:
            outfile.write(self._writeheader())
        try:
            from mar345_IO import compress_pck
        except ImportError, error:
            logger.error("Unable to import mar345_IO to write compressed dataset")
        else:
            compress_pck(self.data, fname)


    def _writeheader(self, linesep="\n"):
        """
        @param linesep: end of line separator
        @return string/bytes containing the mar345 header
        """

        lnsep = len(linesep)


        self.header["HIGH"] = nb_overflow_pixels(self.data)

        binheader = numpy.zeros(16, "int32")
        binheader[:4] = numpy.array([1234, self.dim1, self.header["HIGH"], 1])
        binheader[4] = (self.header.get("MODE", "TIME") == "TIME")
        binheader[5] = self.dim1 * self.dim2
        binheader[6] = int(self.header.get("PIXEL_LENGTH", 1))
        binheader[7] = int(self.header.get("PIXEL_HEIGHT", 1))
        binheader[8] = int(float(self.header.get("WAVELENGTH", 1)) * 1e6)
        binheader[9] = int(float(self.header.get("DISTANCE", 1)) * 1e3)
        binheader[10] = int(float(self.header.get("PHI_START", 1)) * 1e3)
        binheader[11] = int(float(self.header.get("PHI_END", 1)) * 1e3)
        binheader[12] = int(float(self.header.get("OMEGA_START", 1)) * 1e3)
        binheader[13] = int(float(self.header.get("OMEGA_END", 1)) * 1e3)
        binheader[14] = int(float(self.header.get("CHI", 1)) * 1e3)
        binheader[15] = int(float(self.header.get("TWOTHETA", 1)) * 1e3)
        lstOut = [binheader.tostring() + 'mar research'.ljust(64 - lnsep)]
        lstout.append("PROGRAM".ljust(15) + ("FabIO Version %s" % (version)).ljust(49 - lnsep))
        lstout.append("DATE".ljust(15) + time.ctime().ljust(49 - lnsep))
        lstout.append("HIGH" + str(value).ljust(49 - lnsep))
        key = "SCANNER"
        if key in self.header:
            lstout.append(key.ljust(15) + self.header[key].ljust(49 - lnsep))
        key = "FORMAT_TYPE"
        if key in self.header:
            lstout.append("FORMAT".ljust(15) + "%s %s %s" % (self.dim1, self.header[key], self.dim1 * self.dim2).ljust(49 - lnsep))
        key = "HIGH"
        if key in self.header:
            lstout.append(key.ljust(15) + self.header[key].ljust(49 - lnsep))
        key = "PIXEL"
        if key in self.header:
            lstout.append(key.ljust(15) + self.header[key].ljust(49 - lnsep))
        """
PIXEL          LENGTH 150  HEIGHT 150

OFFSET         ROFF 5.000  TOFF 0.000

MULTIPLIER     1.000GAIN           1.000

WAVELENGTH     1.08000

DISTANCE       240.000

RESOLUTION     1.761

PHI            START 0.000  END 1.000  OSC 1

OMEGA          START 0.000  END 0.000  OSC 0

CHI            0.000

TWOTHETA       0.000

CENTER         X 1150.000  Y 1150.000

MODE           TIME

TIME           20.00

COUNTS         START 19.35 END 19.29  NMEAS 9

COUNTS         MIN 19.27  MAX 19.38

COUNTS         AVE 19.30  SIG 0.03

INTENSITY      MIN 1  MAX 249051  AVE 207.8  SIG 951.09

HISTOGRAM      START 0  END 2023  MAX 28307

GENERATOR      ROTATINGANODE  kV 10.0  mA 20.0

MONOCHROMATOR  GRAPHITE  POLAR 0.000

COLLIMATOR     WIDTH 0.30  HEIGHT 0.30

REMARK

END OF HEADER
        """

        return linesep.join(lstOut)


def strpad(str_in, size_out, eol=True):
        size_in = len(str_in)
        if eol:
            str_out = str_in + ' ' * (size_out - size_in - 1) + '\n'
        else:
            str_out = str_in + ' ' * (size_out - size_in)
        return str_out

def nb_overflow_pixels(data):
    mask = data >= 65535
    return len(data[mask])

