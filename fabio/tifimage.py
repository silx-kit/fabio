## Automatically adapted for numpy.oldnumeric Oct 05, 2007 by alter_code1.py

#!/usr/bin/env python
"""

Authors: Henning O. Sorensen & Erik Knudsen
         Center for Fundamental Research: Metal Structures in Four Dimensions
         Risoe National Laboratory
         Frederiksborgvej 399
         DK-4000 Roskilde
         email:henning.sorensen@risoe.dk

mods for fabio by JPW

"""

import Image
import numpy , logging

from fabioimage import fabioimage

TIFF_TO_NUMERIC = { "I;16": numpy.int16 ,

                    }


class tifimage(fabioimage):
    """
    Images in TIF format
    Wraps PIL
    """
    _need_a_seek_to_read = True

    def __init__(self, *args, **kwds):
        """ Tifimage constructor adds an nbits member attribute """
        self.nbits = None
        fabioimage.__init__(self, *args, **kwds)

    def _readheader(self, infile):
        """
        Don't know how to read tiff tags yet...
        """
        try:
            self.header = { "filename" : infile.name }
        except:
            self.header = {}


        # read the first 32 bytes to determine size
        header = numpy.fromstring(infile.read(64), numpy.uint16)
        self.dim1 = int(header[9])
        self.dim2 = int(header[15])
        # nbits is not a fabioimage attribute...
        self.nbits = int(header[21]) # number of bits



    def read(self, fname):
        """
        The fabian read was reading a PIL image
        We convert this to a numpy array
        """
        infile = self._open(fname, "rb")
        self._readheader(infile)
        infile.seek(0)
        try:
            self.pilimage = Image.open(infile)
        except:
            infile.seek(0)
            raw_data = infile.read()
            header_bytes = len(raw_data) - (self.dim1 * self.dim2 * self.nbits) / 8
            if self.nbits == 16: # Probably uint16
#                logging.warn('USING FIT2D 16 BIT TIFF READING - EXPERIMENTAL')
                self.pilimage = Image.frombuffer("F",
                                         (self.dim1, self.dim2),
                                         raw_data[header_bytes:],
                                         "raw",
                                         "I;16",
                                         0, 1)
                self.bpp = 2
                self.data = numpy.fromstring(raw_data[header_bytes:],
                                         numpy.uint16)

            elif self.nbits == 32: # Probably uint16
#                logging.warn('USING FIT2D 32 BIT FLOAT TIFF READING -' + 
#                             ' EXPERIMENTAL')
                self.pilimage = Image.frombuffer("F",
                                         (self.dim1, self.dim2),
                                         raw_data[header_bytes:],
                                         "raw",
                                         "F",
                                         0, 1)
                self.bpp = 4
                self.data = numpy.fromstring(raw_data[header_bytes:],
                                               numpy.float32)
                self.data = numpy.reshape(self.data, (self.dim2, self.dim1))
                self.resetvals()
                return self


        # For some odd reason the getextrema does not work on unsigned 16 bit
        # but it does on 32 bit images, hence convert if 16 bit
        if TIFF_TO_NUMERIC.has_key(self.pilimage.mode) and \
                self.pilimage.mode != "I;16":
            self.data = numpy.fromstring(
                self.pilimage.tostring(),
                TIFF_TO_NUMERIC[self.pilimage.mode])
            self.bpp = len(numpy.ones(1,
                          TIFF_TO_NUMERIC[self.pilimage.mode]).tostring())
        else:
            temp = self.pilimage.convert("I") # 32 bit signed
            self.data = numpy.fromstring(
                temp.tostring(),
                numpy.int32)
            self.bpp = 4
            self.pilimage = temp
        self.dim1, self.dim2 = self.pilimage.size
        # PIL is transposed compared to numpy?
        self.data = numpy.reshape(self.data, (self.dim2, self.dim1))
        self.resetvals()
        return self

    def write(self, fname):
        """
        ... at least try ...
        """
        if self.pilimage is None:
            if self.data.dtype != numpy.dtype('uint16'):
                # Use toPIL16 if you which to save a non 16 bit image 
                # Odd, but this is how it apparently works
                self.toPIL16()
            else:
                # to save 16 bit tif we have to use "I;16" not "F;16"
                size = self.data.shape[:2][::-1]
                self.pilimage = Image.frombuffer('I',
                                                 size,
                                                 self.data.tostring(),
                                                 "raw",
                                                 'I;16',
                                                 0, 1)

        self.pilimage.save(fname, "TIFF")

