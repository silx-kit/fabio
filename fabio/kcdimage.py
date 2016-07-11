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
Authors: Jerome Kieffer, ESRF
         email:jerome.kieffer@esrf.fr

kcd images are 2D images written by the old KappaCCD diffractometer built by Nonius in the 1990's
Based on the edfimage.py parser.
"""
# Get ready for python3:
from __future__ import with_statement, print_function

import numpy, logging
import os, string
from .fabioimage import FabioImage
from .fabioutils import six
logger = logging.getLogger("kcdimage")

DATA_TYPES = {"u16"  :  numpy.uint16 }

MINIMUM_KEYS = [
                # 'ByteOrder', Assume little by default
                'Data type',
                'X dimension',
                'Y dimension',
                'Number of readouts']

DEFAULT_VALUES = { "Data type": "u16" }

if six.PY2:
    ALPHANUM = string.digits + string.letters + ". "
else:
    ALPHANUM = bytes(string.digits + string.ascii_letters + ". ", encoding="ASCII")


class KcdImage(FabioImage):
    """
    Read the Nonius kcd data format """


    def _readheader(self, infile):
        """
        Read in a header in some KCD format from an already open file
        @
        """
        one_line = infile.readline()

        asciiHeader = True
        for oneChar in one_line.strip():
            if not oneChar in ALPHANUM:
                asciiHeader = False


        if asciiHeader is False:
            # This does not look like an KappaCCD file
            logger.warning("First line of %s does not seam to be ascii text!" % infile.name)
        end_of_headers = False
        while not end_of_headers:
            one_line = infile.readline()
            try:
                one_line = one_line.decode("ASCII")
            except UnicodeDecodeError as err:
                end_of_headers = True
            else:
                if len(one_line) > 100:
                    end_of_headers = True
            if not end_of_headers:
                if one_line.strip() == "Binned mode":
                    one_line = "Mode = Binned"
                if "=" in one_line:
                    key, val = one_line.split('=' , 1)
                    key = key.strip()
                    self.header[key] = val.strip()
                else:
                    end_of_headers = True

        missing = []
        for item in MINIMUM_KEYS:
            if item not in self.header:
                missing.append(item)
        if len(missing) > 0:
            logger.debug("KCD file misses the keys " + " ".join(missing))


    def read(self, fname, frame=None):
        """
        Read in header into self.header and
            the data   into self.data
        """
        self.header = self.check_header()
        self.resetvals()
        with self._open(fname, "rb") as infile:
            self._readheader(infile)
            # Compute image size
            try:
                self.dim1 = int(self.header['X dimension'])
                self.dim2 = int(self.header['Y dimension'])
            except:
                raise Exception("KCD file %s is corrupt, cannot read it" % fname)
            try:
                bytecode = DATA_TYPES[self.header['Data type']]
                self.bpp = len(numpy.array(0, bytecode).tostring())
            except KeyError:
                bytecode = numpy.uint16
                self.bpp = 2
                logger.warning("Defaulting type to uint16")
            try:
                nbReadOut = int(self.header['Number of readouts'])
            except KeyError:
                logger.warning("Defaulting number of ReadOut to 1")
                nbReadOut = 1
            fileSize = os.stat(fname)[6]
            expected_size = self.dim1 * self.dim2 * self.bpp * nbReadOut
            infile.seek(fileSize - expected_size)
            block = infile.read()
            assert len(block) == expected_size
        # infile.close()

        # now read the data into the array
        self.data = numpy.zeros((self.dim2, self.dim1), numpy.int32)
        stop = 0
        for i in range(nbReadOut):
            start = stop
            stop = (i + 1) * expected_size // nbReadOut
            data = numpy.fromstring(block[start: stop], bytecode)
            data.shape = self.dim2, self.dim1
            if not numpy.little_endian:
                data.byteswap(True)
            self.data += data
        self.bytecode = self.data.dtype.type
        self.resetvals()
        # ensure the PIL image is reset
        self.pilimage = None
        return self


    @staticmethod
    def checkData(data=None):
        if data is None:
            return None
        else:
            return data.astype(int)


kcdimage = KcdImage
