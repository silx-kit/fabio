#!/usr/bin/env python
"""
Authors: Jerome Kieffer, ESRF 
         email:jerome.kieffer@esrf.fr

kcd images are 2D images written by the old KappaCCD diffractometer built by Nonius in the 1990's
Based on the edfimage.py parser.
"""

import numpy, logging
import os, string
from fabioimage import fabioimage
logger = logging.getLogger("kcdimage")

DATA_TYPES = {"u16"  :  numpy.uint16 }

MINIMUM_KEYS = [
                'ByteOrder',
                'Data type',
                'X dimension',
                'Y dimension',
                'Number of readouts']

DEFAULT_VALUES = { "Data type": "u16" }




class kcdimage(fabioimage):
    """ 
    Read the Nonius kcd data format """


    def _readheader(self, infile):
        """
        Read in a header in some KCD format from an already open file
        @
        """
        oneLine = infile.readline()
        alphanum = string.digits + string.letters + ". "
        asciiHeader = True
        for oneChar in oneLine.strip():
            if not oneChar in alphanum:
                asciiHeader = False


        if asciiHeader is False:
            # This does not look like an edf file
            logger.warning("First line of %s does not seam to be ascii text!" % infile.name)
        endOfHeaders = False
        while not endOfHeaders:
            oneLine = infile.readline()
            if len(oneLine) > 100:
                endOfHeaders = True
                break
            if oneLine.strip() == "Binned mode":
                oneLine = "Mode = Binned"
            try:
                key, val = oneLine.split('=' , 1)
            except:
                endOfHeaders = True
                break
            key = key.strip()
            self.header_keys.append(key)
            self.header[key] = val.strip()
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
        infile = self._open(fname, "rb")
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
        infile.close()

        #now read the data into the array
        self.data = numpy.zeros((self.dim2, self.dim1))
        try:
            for i in range(nbReadOut):
                self.data += numpy.reshape(numpy.fromstring(
                    block[i * expected_size / nbReadOut:(i + 1) * expected_size / nbReadOut], bytecode),
                    [self.dim2, self.dim1])
        except:
            print len(block), bytecode, self.bpp, self.dim2, self.dim1
            raise IOError, \
              'Size spec in kcd-header does not match size of image data field'
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
