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
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

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
from __future__ import absolute_import, print_function, with_statement, division
__authors__ = ["Jérôme Kieffer", "Henning O. Sorensen", "Erik Knudsen"]
__date__ = "05/11/2015"
__license__ = "GPLv3+"
__copyright__ = "ESRF, Grenoble & Risoe National Laboratory"
__status__ = "stable"

import numpy
import logging
logger = logging.getLogger("pnmimage")
from .fabioimage import FabioImage
from .fabioutils import six

SUBFORMATS = [six.b(i) for i in ('P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7')]

HEADERITEMS = [six.b(i) for i in ('SUBFORMAT', 'WIDTH', 'HEIGHT', 'MAXVAL')]
P7HEADERITEMS = [six.b(i) for i in ('WIDTH', 'HEIGHT', 'DEPTH', 'MAXVAL', 'TUPLTYPE', 'ENDHDR')]


class PnmImage(FabioImage):
    def __init__(self, *arg, **kwargs):
        FabioImage.__init__(self, *arg, **kwargs)
        self.header['Subformat'] = 'P5'

    def _readheader(self, f):
        # pnm images have a 3-line header but ignore lines starting with '#'
        # 1st line contains the pnm image sub format
        # 2nd line contains the image pixel dimension
        # 3rd line contains the maximum pixel value (at least for grayscale - check this)

        l = f.readline().strip()

        if l not in SUBFORMATS:
            raise IOError('unknown subformat of pnm: %s' % l)
        else:
            self.header[six.b('SUBFORMAT')] = l

        if self.header[six.b('SUBFORMAT')] == 'P7':
            # this one has a special header
            while six.b('ENDHDR') not in l:
                l = f.readline()
                while(l[0] == '#'): l = f.readline()
                s = l.lsplit(' ', 1)
                if s[0] not in P7HEADERITEMS:
                    raise IOError('Illegal pam (netpnm p7) headeritem %s' % s[0])
                self.header[s[0]] = s[1]
        else:
            values = list(l.split())
            while len(values) < len(HEADERITEMS):
                l = f.readline()
                while l[0] == '#':
                    l = f.readline()
                values += l.split()
            for k, v in zip(HEADERITEMS, values):
                self.header[k] = v.strip()

        # set the dimensions
        self.dim1 = int(self.header[six.b("WIDTH")])
        self.dim2 = int(self.header[six.b("HEIGHT")])
        # figure out how many bytes are used to store the data
        # case construct here!
        m = int(self.header[six.b('MAXVAL')])
        if m < 256:
            self.bytecode = numpy.uint8
        elif m < 65536:
            self.bytecode = numpy.uint16
        elif m < 2147483648:
            self.bytecode = numpy.uint32
            logger.warning('32-bit pixels are not really supported by the netpgm standard')
        else:
            raise IOError('could not figure out what kind of pixels you have')

    def read(self, fname, frame=None):
        """
        try to read PNM images
        @param fname: name of the file
        @param frame: not relevant here! PNM is always single framed
        """
        self.header = self.check_header()
        self.resetvals()
        infile = self._open(fname)
        self._readheader(infile)

        # read the image data
        if six.PY3:
            format = str(self.header[six.b('SUBFORMAT')], encoding="latin-1")
        else:
            format = self.header[six.b('SUBFORMAT')]
        decoder_name = "%sdec" % format
        if decoder_name in dir(PnmImage):
            decoder = getattr(PnmImage, decoder_name)
            self.data = decoder(self, infile, self.bytecode)
        else:
            raise IOError("No decoder named %s for file %s" % (decoder_name, fname))
        self.resetvals()
        return self

    def write(self, fname):
        """
        try to write image. For now, limited to
        @param fname: name of the file
        """
        self.header[six.b("SUBFORMAT")] = "P5"
        self.header[six.b("WIDTH")] = self.dim1
        self.header[six.b("HEIGHT")] = self.dim2
        self.header[six.b("MAXVAL")] = self.data.max()
        header = six.b(" ".join([str(self.header[key]) for key in HEADERITEMS[1:]]))
        with open(fname, "wb") as fobj:
            fobj.write(six.b("P5 \n"))
            fobj.write(header)
            fobj.write(six.b(" \n"))
            if numpy.little_endian:
                fobj.write(self.data.byteswap().tostring())
            else:
                fobj.write(self.data.tostring())

    def P1dec(self, buf, bytecode):
        data = numpy.zeros((self.dim2, self.dim1))
        i = 0
        for l in buf:
            try:
                data[i, :] = numpy.array(l.split()).astype(bytecode)
            except ValueError:
                raise IOError('Size spec in pnm-header does not match size of image data field')
        return data

    def P4dec(self, buf, bytecode):
        err = 'single bit (pbm) images are not supported - yet'
        logger.error(err)
        raise NotImplementedError(err)

    def P2dec(self, buf, bytecode):
        data = numpy.zeros((self.dim2, self.dim1))
        i = 0
        for l in buf:
            try:
                data[i, :] = numpy.array(l.split()).astype(bytecode)
            except ValueError:
                raise IOError('Size spec in pnm-header does not match size of image data field')
        return data

    def P5dec(self, buf, bytecode):
        l = buf.read()
        try:
            data = numpy.fromstring(l, bytecode)
        except ValueError:
            raise IOError('Size spec in pnm-header does not match size of image data field')
        data.shape = self.dim2, self.dim1
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
