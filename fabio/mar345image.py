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
import numpy, struct, string, time, sys
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
            if m == 'END OF HEADER':
                break
            n = m.split(' ', 1)
            if n[0] == '':
                continue
            logger.debug("reading: %s %s", n[0], n[1])
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
            outfile.write(self._high_intensity_pixel_records())
        try:
            from mar345_IO import compress_pck
        except ImportError, error:
            logger.error("Unable to import mar345_IO to write compressed dataset")
        else:
            compress_pck(self.data, fname)


    def _writeheader(self, linesep="\n", size=4096):#the standard padding does not inclued
        """
        @param linesep: end of line separator
        @return string/bytes containing the mar345 header
        """
        try:
            version = sys.modules["fabio"].version
        except:
            version = "0.0.9"
        lnsep = len(linesep)


        self.header["HIGH"] = nb_overflow_pixels(self.data)

        binheader = numpy.zeros(16, "int32")
        binheader[:4] = numpy.array([1234, self.dim1, int(self.header["HIGH"]), 1])
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
        lstout = [binheader.tostring() + 'mar research'.ljust(64 - lnsep)]

        lstout.append("PROGRAM".ljust(15) + ("FabIO Version %s" % (version)).ljust(49 - lnsep))
        lstout.append("DATE".ljust(15) + time.ctime().ljust(49 - lnsep))
        key = "SCANNER"
        if key in self.header:
            lstout.append(key.ljust(15) + str(self.header[key]).ljust(49 - lnsep))
        key = "FORMAT_TYPE"
        if key in self.header:
            lstout.append("FORMAT".ljust(15) + ("%s  %s %s" % (self.dim1, self.header[key], self.dim1 * self.dim2)).ljust(49 - lnsep))
        key = "HIGH"
        if key in self.header:
            lstout.append(key.ljust(15) + str(self.header[key]).ljust(49 - lnsep))
        key = "PIXEL"
        if key in self.header:
            lstout.append(key.ljust(15) + str(self.header[key]).ljust(49 - lnsep))
        key1 = "OFFSET_ROFF"
        key2 = "OFFSET_TOFF"
        if key1 in self.header and key2 in self.header:
             lstout.append("OFFSET".ljust(15) + ("ROFF %s  TOFF %s" % (self.header[key1], self.header[key2])).ljust(49 - lnsep))
        key = "MULTIPLIER"
        if key in self.header:
            lstout.append(key.ljust(15) + str(self.header[key]).ljust(49 - lnsep))
        key = "GAIN"
        if key in self.header:
            lstout.append(key.ljust(15) + str(self.header[key]).ljust(49 - lnsep))
        key = "WAVELENGTH"
        if key in self.header:
            lstout.append(key.ljust(15) + str(self.header[key]).ljust(49 - lnsep))
        key = "DISTANCE"
        if key in self.header:
            lstout.append(key.ljust(15) + str(self.header[key]).ljust(49 - lnsep))
        key = "RESOLUTION"
        if key in self.header:
            lstout.append(key.ljust(15) + str(self.header[key]).ljust(49 - lnsep))
        key1 = "PHI_START"
        key2 = "PHI_END"
        key3 = "PHI_OSC"
        if (key1 in self.header) and (key2 in self.header) and (key3 in self.header):
            lstout.append("PHI".ljust(15) + ("START %s  END %s  OSC %s" % (self.header[key1], self.header[key2], self.header[key3])).ljust(49 - lnsep))
        key1 = "OMEGA_START"
        key2 = "OMEGA_END"
        key3 = "OMEGA_OSC"
        if (key1 in self.header) and (key2 in self.header) and (key3 in self.header):
            lstout.append("OMEGA".ljust(15) + ("START %s  END %s  OSC %s" % (self.header[key1], self.header[key2], self.header[key3])).ljust(49 - lnsep))
        key = "CHI"
        if key in self.header:
            lstout.append(key.ljust(15) + str(self.header[key]).ljust(49 - lnsep))
        key = "TWOTHETA"
        if key in self.header:
            lstout.append(key.ljust(15) + str(self.header[key]).ljust(49 - lnsep))
        key1 = "CENTER_X"
        key2 = "CENTER_Y"
        if (key1 in self.header) and (key2 in self.header):
             lstout.append("CENTER".ljust(15) + ("X %s  Y %s" % (self.header[key1], self.header[key2])).ljust(49 - lnsep))
        key = "MODE"
        if key in self.header:
            lstout.append(key.ljust(15) + str(self.header[key]).ljust(49 - lnsep))
        key = "TIME"
        if key in self.header:
            lstout.append(key.ljust(15) + str(self.header[key]).ljust(49 - lnsep))
        key1 = "COUNTS_START"
        key2 = "COUNTS_END"
        key3 = "COUNTS_NMEAS"
        if key1 in self.header and key2 in self.header and key3 in self.header:
            lstout.append("COUNTS".ljust(15) + ("START %s  END %s  NMEAS %s" % (self.header[key1], self.header[key2], self.header[key3])).ljust(49 - lnsep))
        key1 = "COUNTS_MIN"
        key2 = "COUNTS_MAX"
        if key1 in self.header and key2 in self.header:
             lstout.append("COUNTS".ljust(15) + ("MIN %s  MAX %s" % (self.header[key1], self.header[key2])).ljust(49 - lnsep))
        key1 = "COUNTS_AVE"
        key2 = "COUNTS_SIG"
        if key1 in self.header and key2 in self.header:
             lstout.append("COUNTS".ljust(15) + ("AVE %s  SIG %s" % (self.header[key1], self.header[key2])).ljust(49 - lnsep))
        key1 = "INTENSITY_MIN"
        key2 = "INTENSITY_MAX"
        key3 = "INTENSITY_AVE"
        key4 = "INTENSITY_SIG"
        if key1 in self.header and key2 in self.header and key3 in self.header and key4 in self.header:
            lstout.append("INTENSITY".ljust(15) + ("MIN %s  MAX %s  AVE %s  SIG %s" % (self.header[key1], self.header[key2], self.header[key3], self.header[key4])).ljust(49 - lnsep))
        key1 = "HISTOGRAM_START"
        key2 = "HISTOGRAM_END"
        key3 = "HISTOGRAM_MAX"
        if key1 in self.header and key2 in self.header and key3 in self.header:
            lstout.append("HISTOGRAM".ljust(15) + ("START %s  END %s  MAX %s" % (self.header[key1], self.header[key2], self.header[key3])).ljust(49 - lnsep))
        key = "GENERATOR"
        if key in self.header:
            lstout.append(key.ljust(15) + str(self.header[key]).ljust(49 - lnsep))
        key = "MONOCHROMATOR"
        if key in self.header:
            lstout.append(key.ljust(15) + str(self.header[key]).ljust(49 - lnsep))
        key1 = "COLLIMATOR_WIDTH"
        key2 = "COLLIMATOR_HEIGHT"
        if key1 in self.header and key2 in self.header:
             lstout.append("COLLIMATOR".ljust(15) + ("WIDTH %s  HEIGHT %s" % (self.header[key1], self.header[key2])).ljust(49 - lnsep))
        key = "REMARK"
        if key in self.header:
            lstout.append(key.ljust(15) + str(self.header[key]).ljust(49 - lnsep))
        else:
            lstout.append(key.ljust(64 - lnsep))
        key = "END OF HEADER"
        lstout.append(key)

        return linesep.join(lstout).ljust(size)
        
	
    def deprecated_high_intensity_pixel_records(self):
        flt_data = self.data.flatten()
        pix_location = numpy.where(flt_data > 65535)[0]
        records = [numpy.zeros(8, "int32")]
        record_number = 0
        pix_num = 0
        for i in pix_location:
            if pix_num <= 6:
                records[record_number][pix_num] = i+1
                records[record_number][pix_num + 1] = flt_data[i]
                pix_num += 2
            else:
                records += [numpy.zeros(8, "int32")]
                record_number += 1
                records[record_number][0] = i+1
                records[record_number][1] = flt_data[i]
                pix_num = 2
        return numpy.array(records,"int32").tostring()

    def _high_intensity_pixel_records(self):
        flt_data = self.data.flatten()
        pix_location = numpy.where(flt_data > 65535)[0]
        nb_pix = pix_location.size
        tmp = numpy.zeros((nb_pix,2), dtype = "int32")
        tmp[:,0]=pix_location
        tmp[:,1]=flt_data[pix_location]
        if nb_pix%4==0:
        	tmp2=tmp
       	else:
       		tmp2 = numpy.zeros(((nb_pix//4+1)*4,2),dtype="int32")
       		tmp2[:nb_pix,:]=tmp
        return tmp2.tostring()
        
def nb_overflow_pixels(data):
    return (data > 65535).sum()
    
    
