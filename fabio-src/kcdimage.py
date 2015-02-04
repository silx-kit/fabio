#!/usr/bin/env python
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
from .fabioimage import fabioimage
logger = logging.getLogger("kcdimage")
from .third_party import six
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


class kcdimage(fabioimage):
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
                    self.header_keys.append(key)
                    self.header[key] = val.strip()
                else:
                    end_of_headers = True

        missing = []
        for item in MINIMUM_KEYS:
            if item not in self.header_keys:
                missing.append(item)
        if len(missing) > 0:
            logger.debug("KCD file misses the keys " + " ".join(missing))


    def read(self, fname, frame=None):
        """
        Read in header into self.header and
            the data   into self.data
        """
        self.header = {}
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
