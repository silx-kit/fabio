#!/usr/bin/env python
#coding: utf-8
"""

Authors: Henning O. Sorensen & Erik Knudsen
         Center for Fundamental Research: Metal Structures in Four Dimensions
         Risoe National Laboratory
         Frederiksborgvej 399
         DK-4000 Roskilde
         email:henning.sorensen@risoe.dk

* Jérôme Kieffer:
  European Synchrotron Radiation Facility;
  Grenoble (France)

License: GPLv3+
"""
# Get ready for python3:
from __future__ import with_statement, print_function, division

__authors__ = ["Jérôme Kieffer", "Henning O. Sorensen", "Erik Knudsen"]
__date__ = "12/09/2014"
__license__ = "GPLv3+"
__copyright__ = "ESRF, Grenoble & Risoe National Laboratory"
__status__ = "stable"

import numpy
import logging
logger = logging.getLogger("pnmimage")
from .fabioimage import fabioimage

SUBFORMATS = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7']

HEADERITEMS = ['SUBFORMAT', 'WIDTH', 'HEIGHT', 'MAXVAL']
P7HEADERITEMS = ['WIDTH', 'HEIGHT', 'DEPTH', 'MAXVAL', 'TUPLTYPE', 'ENDHDR']

class pnmimage(fabioimage):
    def __init__(self, *arg, **kwargs):
        fabioimage.__init__(self, *arg, **kwargs)
        fun = getattr(fabioimage, '__init__', lambda x: None)
        fun(self)
        self.data = None
        self.header = {'Subformat':'P5'}
        self.dim1 = self.dim2 = 0
        self.m = self.maxval = self.stddev = self.minval = None
        self.header_keys = self.header.keys()
        self.bytecode = None

    def _readheader(self, f):
        #pnm images have a 3-line header but ignore lines starting with '#'
        #1st line contains the pnm image sub format
        #2nd line contains the image pixel dimension
        #3rd line contains the maximum pixel value (at least for grayscale - check this)

        l = f.readline().strip()
        if l not in SUBFORMATS:
            raise IOError, ('unknown subformat of pnm: %s' % l)
        else:
            self.header['SUBFORMAT'] = l

        if self.header['SUBFORMAT'] == 'P7':
            self.header_keys = P7HEADERITEMS
            #this one has a special header
            while 'ENDHDR' not in l:
                l = f.readline()
                while(l[0] == '#'): l = f.readline()
                s = l.lsplit(' ', 1)
                if s[0] not in P7HEADERITEMS:
                    raise IOError, ('Illegal pam (netpnm p7) headeritem %s' % s[0])
                self.header[s[0]] = s[1]
        else:
            self.header_keys = HEADERITEMS
            values = list(l.split())
            while len(values) < len(self.header_keys):
                l = f.readline()
                while l[0] == '#':
                    l = f.readline()
                values += l.split()
            for k, v in zip(self.header_keys, values):
                self.header[k] = v.strip()

        #set the dimensions
        self.dim1 = int(self.header["WIDTH"])
        self.dim2 = int(self.header["HEIGHT"])
        #figure out how many bytes are used to store the data
        #case construct here!
        m = int(self.header['MAXVAL'])
        if m < 256:
            self.bytecode = numpy.uint8
        elif m < 65536:
            self.bytecode = numpy.uint16
        elif m < 2147483648L:
            self.bytecode = numpy.uint32
            logger.warning('32-bit pixels are not really supported by the netpgm standard')
        else:
            raise IOError, 'could not figure out what kind of pixels you have'

    def read(self, fname, frame=None):
        """
        try to read PNM images
        @param fname: name of the file
        @param frame: not relevant here! PNM is always single framed
        """
        self.header = {}
        self.resetvals()
        infile = self._open(fname)
        self._readheader(infile)

        #read the image data
        decoder_name = "%sdec" % self.header['SUBFORMAT']
        if decoder_name in dir(pnmimage):
            decoder = getattr(pnmimage, decoder_name)
            self.data = decoder(self, infile, self.bytecode)
        else:
            raise IOError("No decoder named %s for file %s" % (decoder_name, fname))
        self.resetvals()
        return self

    def P1dec(self, buf, bytecode):
        data = numpy.zeros((self.dim2, self.dim1))
        i = 0
        for l in buf.readlines():
            try:
                data[i, :] = numpy.array(l.split()).astype(bytecode)
            except ValueError:
                raise IOError, 'Size spec in pnm-header does not match size of image data field'
        return data

    def P4dec(self, buf, bytecode):
        err = 'single bit (pbm) images are not supported - yet'
        logger.error(err)
        raise NotImplementedError(err)

    def P2dec(self, buf, bytecode):
        data = numpy.zeros((self.dim2, self.dim1))
        i = 0
        for l in buf.readlines():
            try:
                data[i, :] = numpy.array(l.split()).astype(bytecode)
            except ValueError:
                raise IOError, 'Size spec in pnm-header does not match size of image data field'
        return data

    def P5dec(self, buf, bytecode):
        l = buf.read()
        try:
            npa = numpy.fromstring(l, bytecode)
            npa.shape = self.dim2, self.dim1
            data = npa.byteswap()
        except ValueError:
            raise IOError, 'Size spec in pnm-header does not match size of image data field'
        return data

    def P3dec(self, buf, bytecode):
        err = '(plain-ppm) RGB images are not supported - yet'
        logger.error(err)
        raise NotImplementedError(err)

    def P6dec(self, buf, bytecode):
        err = '(ppm) RGB images are not supported - yet'
        logger.error(err)
        raise NotImplementedError(err)

    def P7dec(self, buf, bytecode):
        err = '(pam) images are not supported - yet'
        logger.error(err)
        raise NotImplementedError(err)

    def write(self, filename):
        raise NotImplementedError('write pnm images is not implemented yet.')

    @staticmethod
    def checkData(data=None):
        if data is None:
            return None
        else:
            return data.astype(int)
