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
         email:erik.knudsen@risoe.dk

+ mods for fabio by JPW

"""

from __future__ import with_statement, print_function
import numpy
import logging
from .fabioimage import FabioImage
from .fabioutils import to_str
logger = logging.getLogger(__name__)


class AdscImage(FabioImage):
    """ Read an image in ADSC format (quite similar to edf?) """

    DESCRIPTION = "ADSC format (from Area Detector Systems Corporation)"

    DEFAULT_EXTENSIONS = ["img"]

    def __init__(self, *args, **kwargs):
        FabioImage.__init__(self, *args, **kwargs)

    def read(self, fname, frame=None):
        """ read in the file """
        with self._open(fname, "rb") as infile:
            try:
                self._readheader(infile)
            except Exception:
                logger.debug("Backtrace", exc_info=True)
                raise Exception("Error processing ADSC header")
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
        # infile.close()

        # NOTE: Used by the d*TREK format
        data_mode = self.header.get("PXD_DETECTOR_ACQUISITION_DATAMODE", None)
        if data_mode == "Combined 31bit":
            dtype = numpy.dtype(numpy.uint32)
        else:
            dtype = numpy.dtype(numpy.uint16)

        # now read the data into the array
        self._shape = int(self.header['SIZE2']), int(self.header['SIZE1'])
        data = numpy.frombuffer(binary, dtype).copy()
        if self.swap_needed():
            data.byteswap(True)
        try:
            data.shape = self._shape
        except ValueError:
                raise IOError('Size spec in ADSC-header does not match ' +
                              'size of image data field %s != %s' % (self._shape, data.size))
        self.data = data
        self._shape = None
        self._dtype = None
        self.resetvals()
        return self

    def _readheader(self, infile):
        """ read an adsc header """
        line = infile.readline()
        bytesread = len(line)
        while line != b'}\n':
            if b'=' in line:
                (key, val) = to_str(line).split('=')
                self.header[key.strip()] = val.strip(' ;\n\r')
            line = infile.readline()
            bytesread = bytesread + len(line)

    def write(self, fname):
        """
        Write adsc format
        """
        out = b'{\n'
        for key in self.header:
            out += b"%s = %s;\n" % (key, self.header[key])
        if "HEADER_BYTES" in self.header:
            pad = int(self.header["HEADER_BYTES"]) - len(out) - 2
        else:
            # hsize = ((len(out) + 23) // 512 + 1) * 512
            hsize = (len(out) + 533) & ~(512 - 1)
            out += b"HEADER_BYTES=%d;\n" % (hsize)
            pad = hsize - len(out) - 2
        out += pad * b' ' + b"}\n"
        assert len(out) % 512 == 0, "Header is not multiple of 512"

        data = self.data.astype(numpy.uint16)
        if self.swap_needed():
            data.byteswap(True)

        with open(fname, "wb") as outf:
            outf.write(out)
            outf.write(data.tostring())
        # outf.close()

    def swap_needed(self):
        if "BYTE_ORDER" not in self.header:
            logger.warning("No byte order specified, assuming little_endian")
            BYTE_ORDER = "little_endian"
        else:
            BYTE_ORDER = self.header["BYTE_ORDER"]
        if "little" in BYTE_ORDER and numpy.little_endian:
            return False
        elif "big" in BYTE_ORDER and not numpy.little_endian:
            return False
        elif "little" in BYTE_ORDER and not numpy.little_endian:
            return True
        elif "big" in BYTE_ORDER and numpy.little_endian:
            return True


adscimage = AdscImage
