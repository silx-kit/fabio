# coding: utf-8
#
#    Project: X-ray image reader
#             https://github.com/silx-kit/fabio
#
#
#    Copyright (C) European Synchrotron Radiation Facility, Grenoble, France
#
#    Principal author:       Jérôme Kieffer (Jerome.Kieffer@ESRF.eu)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE

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

License: MIT
"""

__authors__ = ["Jérôme Kieffer", "Henning O. Sorensen", "Erik Knudsen"]
__date__ = "18/12/2020"
__license__ = "MIT"
__copyright__ = "ESRF, Grenoble & Risoe National Laboratory"
__status__ = "stable"

import io
import logging
import numpy

logger = logging.getLogger(__name__)
from .fabioimage import FabioImage

SUBFORMATS = (b'P1', b'P2', b'P3', b'P4', b'P5', b'P6', b'P7')
HEADERITEMS = (b'SUBFORMAT', b'WIDTH', b'HEIGHT', b'MAXVAL')
P7HEADERITEMS = (b'WIDTH', b'HEIGHT', b'DEPTH', b'MAXVAL', b'TUPLTYPE', b'ENDHDR')


class PnmImage(FabioImage):

    DESCRIPTION = "PNM file format"

    DEFAULT_EXTENSIONS = ["pnm", "pgm", "pbm"]

    def __init__(self, *arg, **kwargs):
        FabioImage.__init__(self, *arg, **kwargs)
        self.header['Subformat'] = 'P5'

    def _readheader(self, f):
        # pnm images have a 3-line header but ignore lines starting with '#'
        # 1st line contains the pnm image sub format
        # 2nd line contains the image pixel dimension
        # 3rd line contains the maximum pixel value (at least for grayscale - check this)

        line = f.readline().strip()
        if line not in SUBFORMATS:
            raise IOError('unknown subformat of pnm: %s' % line)
        else:
            self.header[b'SUBFORMAT'] = line

        if self.header[b'SUBFORMAT'] == 'P7':
            # this one has a special header
            while b'ENDHDR' not in line:
                line = f.readline()
                while(line[0] == '#'):
                    line = f.readline()
                s = line.lsplit(' ', 1)
                if s[0] not in P7HEADERITEMS:
                    raise IOError('Illegal pam (netpnm p7) headeritem %s' % s[0])
                self.header[s[0]] = s[1]
        else:
            values = list(line.split())
            while len(values) < len(HEADERITEMS):
                line = f.readline()
                while line[0] == '#':
                    line = f.readline()
                values += line.split()
            for k, v in zip(HEADERITEMS, values):
                self.header[k] = v.strip()

        # set the dimensions
        dim1 = int(self.header[b"WIDTH"])
        dim2 = int(self.header[b"HEIGHT"])
        self._shape = dim2, dim1
        # figure out how many bytes are used to store the data
        # case construct here!
        m = int(self.header[b'MAXVAL'])
        if m < 256:
            self._dtype = numpy.dtype(numpy.uint8)
        elif m < 65536:
            self._dtype = numpy.dtype(numpy.uint16)
        elif m < 2147483648:
            self._dtype = numpy.dtype(numpy.uint32)
            logger.warning('32-bit pixels are not really supported by the netpgm standard')
        else:
            raise IOError('could not figure out what kind of pixels you have')

    def read(self, fname, frame=None):
        """
        try to read PNM images
        :param fname: name of the file
        :param frame: not relevant here! PNM is always single framed
        """
        self.header = self.check_header()
        self.resetvals()
        infile = self._open(fname)
        self._readheader(infile)

        # read the image data
        fmt = str(self.header[b'SUBFORMAT'], encoding="latin-1")
        decoder_name = "%sdec" % fmt
        if decoder_name in dir(PnmImage):
            decoder = getattr(PnmImage, decoder_name)
            self.data = decoder(self, infile, self._dtype)
        else:
            raise IOError("No decoder named %s for file %s" % (decoder_name, fname))
        self.resetvals()
        return self

    def write(self, fname):
        """
        try to write image. For now, limited to
        :param fname: name of the file
        """
        self.header[b"SUBFORMAT"] = "P5"
        self.header[b"WIDTH"] = self.shape[-1]
        self.header[b"HEIGHT"] = self.shape[-2]
        self.header[b"MAXVAL"] = self.data.max()
        header = (" ".join([str(self.header[key]) for key in HEADERITEMS[1:]])).encode("latin-1")
        with self._open(fname, "wb") as fobj:
            fobj.write(b"P5 \n")
            fobj.write(header)
            fobj.write(b" \n")
            if isinstance(fobj, io.BufferedWriter):
                if numpy.little_endian:
                    self.data.byteswap().tofile(fobj)
                else:
                    self.data.tofile(fobj)
            else:
                if numpy.little_endian:
                    fobj.write(self.data.byteswap().tobytes())
                else:
                    fobj.write(self.data.tobytes())

    def P1dec(self, buf, bytecode):
        data = numpy.zeros(self.shape)
        i = 0
        for l in buf:
            try:
                data[i,:] = numpy.array(l.split()).astype(bytecode)
            except ValueError:
                raise IOError('Size spec in pnm-header does not match size of image data field')
        return data

    def P4dec(self, buf, bytecode):
        err = 'single bit (pbm) images are not supported - yet'
        logger.error(err)
        raise NotImplementedError(err)

    def P2dec(self, buf, bytecode):
        data = numpy.zeros(self.shape)
        i = 0
        for l in buf:
            try:
                data[i,:] = numpy.array(l.split()).astype(bytecode)
            except ValueError:
                raise IOError('Size spec in pnm-header does not match size of image data field')
        return data

    def P5dec(self, buf, bytecode):
        data = buf.read()
        try:
            data = numpy.frombuffer(data, bytecode).copy()
        except ValueError:
            raise IOError('Size spec in pnm-header does not match size of image data field')
        data.shape = self.shape
        if numpy.little_endian:
            data.byteswap(True)
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

    @staticmethod
    def check_data(data=None):
        if data is None:
            return None
        else:
            data = data.clip(0, 65535)
            if data.max() < 256:
                return data.astype(numpy.uint8)
            else:
                return data.astype(numpy.uint16)


pnmimage = PnmImage
