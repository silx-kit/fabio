#!/usr/bin/env python
#coding: utf8
"""

Authors: Henning O. Sorensen & Erik Knudsen
         Center for Fundamental Research: Metal Structures in Four Dimensions
         Risoe National Laboratory
         Frederiksborgvej 399
         DK-4000 Roskilde
         email:henning.sorensen@risoe.dk

"""

import numpy, logging
logger = logging.getLogger("pnmimage")
from fabioimage import fabioimage

SUBFORMATS = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7']

HEADERITEMS = ['SUBFORMAT', 'DIMENSIONS', 'MAXVAL']
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
        self.header_keys = ['SUBFORMAT', 'DIMENSIONS', 'MAXVAL']

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
            for k in self.header_keys[1:]:
                l = f.readline()
                while(l[0] == '#'): l = f.readline()
                self.header[k] = l.strip()

        #set the dimensions
        dims = (self.header['DIMENSIONS'].split())
        self.dim1, self.dim2 = int(dims[0]), int(dims[1])
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
            self.data = decoder(infile, self.bytecode)
        else:
            raise IOError("No decoder named %s for file %s" % (decoder_name, fname))
        self.resetvals()
        return self

    @staticmethod
    def P1dec(buf, bytecode):
        data = numpy.zeros((self.dim2, self.dim1))
        i = 0
        for l in buf.readlines():
            try:
                data[i, :] = numpy.array(l.split()).astype(bytecode)
            except ValueError:
                raise IOError, 'Size spec in pnm-header does not match size of image data field'
        return data

    @staticmethod
    def P4dec(buf, bytecode):
        err = 'single bit (pbm) images are not supported - yet'
        logger.error(err)
        raise NotImplementedError(err)

    @staticmethod
    def P2dec(buf, bytecode):
        data = numpy.zeros((self.dim2, self.dim1))
        i = 0
        for l in buf.readlines():
            try:
                data[i, :] = numpy.array(l.split()).astype(bytecode)
            except ValueError:
                raise IOError, 'Size spec in pnm-header does not match size of image data field'
        return data

    @staticmethod
    def P5dec(buf, bytecode):
        l = buf.read()
        try:
            data = numpy.reshape(numpy.fromstring(l, bytecode), [self.dim2, self.dim1]).byteswap()
        except ValueError:
            raise IOError, 'Size spec in pnm-header does not match size of image data field'
        return data

    @staticmethod
    def P3dec(buf, bytecode):
        err = '(plain-ppm) RGB images are not supported - yet'
        logger.error(err)
        raise NotImplementedError(err)

    @staticmethod
    def P6dec(buf, bytecode):
        err = '(ppm) RGB images are not supported - yet'
        logger.error(err)
        raise NotImplementedError(err)

    @staticmethod
    def P7dec(buf, bytecode):
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
