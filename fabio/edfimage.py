# Automatically adapted for numpy.oldnumeric Oct 05, 2007 by alter_code1.py

#!/usr/bin/env python
"""
Authors: Henning O. Sorensen & Erik Knudsen
         Center for Fundamental Research: Metal Structures in Four Dimensions
         Risoe National Laboratory
         Frederiksborgvej 399
         DK-4000 Roskilde
         email:erik.knudsen@risoe.dk

        + Jon Wright, ESRF
"""

import numpy as np, logging

from fabio.fabioimage import fabioimage


DATA_TYPES = {  "SignedByte"     :  np.int8,
                "UnsignedByte"   :  np.uint8,
                "SignedShort"    :  np.int16,
                "UnsignedShort"  :  np.uint16,
                "UnsignedShortInteger" : np.uint16,
                "SignedInteger"  :  np.int32,
                "UnsignedInteger":  np.uint32,
                "SignedLong"     :  np.int32,
                "UnsignedLong"   :  np.uint32,
                "FloatValue"     :  np.float32,
                "FLOATVALUE"     :  np.float32,                
                "FLOAT"          :  np.float32, # fit2d
                "Float"          :  np.float32, # fit2d
                "DoubleValue"    :  np.float
                }

MINIMUM_KEYS = ['HeaderID',
                'Image',
                'ByteOrder',
                'DataType',
                'Dim_1',
                'Dim_2',
                'Size'] # Size is thought to be essential for writing at least

DEFAULT_VALUES = {"HeaderID":  "EH:000001:000000:000000",
                  "Image":   "1",
                  "ByteOrder":  "LowByteFirst", # FIXME?
                  "DataType": "FLOAT"
                  }




class edfimage(fabioimage):
    """ Read and try to write the ESRF edf data format """


    def _readheader(self, infile):
        """
        Read in a header in some EDF format from an already open file

        TODO : test for minimal attributes?
        """
        BLOCKSIZE = 512
        block = infile.read(BLOCKSIZE)
        if block[:4].find("{") < 0 :
            # This does not look like an edf file
            logging.warning("no opening {. Corrupt header of EDF file " + \
                            str(infile.name))

        while '}' not in block:
            block = block + infile.read(BLOCKSIZE)
            if len(block) > BLOCKSIZE * 20:
                raise Exception("Runaway header in EDF file")
        start , end = block.find("{") + 1, block.find("}")
        for line in block[start:end].split(';'):
            if '=' in line:
                key, val = line.split('=' , 1)
                # Users cannot type in significant whitespace
                key = key.rstrip().lstrip()
                self.header_keys.append(key)
                self.header[key] = val.lstrip().rstrip()
        missing = []
        for item in MINIMUM_KEYS:
            if item not in self.header_keys:
                missing.append(item)
        if len(missing) > 0:
            logging.debug("EDF file misses the keys " + " ".join(missing))

    def read(self, fname):
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
            self.dim1 = int(self.header['Dim_1'])
            self.dim2 = int(self.header['Dim_2'])
        except:
            raise Exception("EDF file", str(fname) + \
                                "is corrupt, cannot read it")
        try:
            bytecode = DATA_TYPES[self.header['DataType']]
        except KeyError:
            bytecode = np.uint16
            logging.warning("Defaulting type to uint16")
        self.bpp = len(np.array(0, bytecode).tostring())

        # Sorry - this was a safe way to read old ID11 imagepro edfs
        # assumes corrupted headers are shorter, they could be longer
        if self.header.has_key('Image') and self.header['Image'] != '1':
            logging.warning("Could be a multi-image file")
        block = infile.read()
        expected_size = self.dim1 * self.dim2 * self.bpp

        if len(block) != expected_size:
            # The binary which has been read in does not match the size 
            # expected. Two cases are known:
            ####    1 extra byte (\0) at the end of the header (ImagePro)
            ####    Padding to 512 bytes, image is at the beginning 
            # These overlap in the case of an image of, eg:
            #       1024x1024-1 == 825x1271
            # To distinguish, we look for a header key:
            padded = False
            nbytesread = len(block)
            if self.header.has_key("EDF_BinarySize"):
                if int(self.header["EDF_BinarySize"]) == nbytesread:
                    padded = True
            if self.header.has_key("Size"):
                if int(self.header["Size"]) == nbytesread:
                    padded = True
            if padded:
                block = block[:expected_size]
                if self.header.has_key("EDF_BlockBoundary"):
                    chunksize = int(self.header["EDF_BlockBoundary"])
                else:
                    chunksize = 512
                if nbytesread % chunksize != 0:
                    # Unexpected padding
                    logging.warning("EDF file is strangely padded, size " +
                            str(nbytesread) + " is not multiple of " +
                            str(chunksize) + ", please verify your image")
            else: # perhaps not padded                
                # probably header overspill (\0)
                logging.warning("Read too many bytes, got " + str(len(block)) + \
                                " want " + str(expected_size))
                block = block[-expected_size:]
        if len(block) < expected_size:
            # FIXME
            logging.warning("Padded")
        infile.close()

        #now read the data into the array
        try:
            self.data = np.reshape(
                np.fromstring(block, bytecode),
                [self.dim2, self.dim1])
        except:
            print len(block), bytecode, self.bpp, self.dim2, self.dim1
            raise IOError, \
              'Size spec in edf-header does not match size of image data field'
        self.bytecode = self.data.dtype.type
        swap = self.swap_needed()
        if swap:
            self.data = self.data.byteswap()
            # Remove verbose arg - use logging and levels
            logging.info('Byteswapped from ' + self.header['ByteOrder'])
        else:
            logging.info('using ' + self.header['ByteOrder'])
        self.resetvals()
        # ensure the PIL image is reset
        self.pilimage = None
        return self

    def swap_needed(self):
        """
        Decide if we need to byteswap
        """
        if ('Low'  in self.header['ByteOrder'] and np.little_endian) or \
           ('High' in self.header['ByteOrder'] and not np.little_endian):
            return False
        if ('High'  in self.header['ByteOrder'] and np.little_endian) or \
           ('Low' in self.header['ByteOrder'] and not np.little_endian):
            if self.bpp in [2, 4, 8]:
                return True
            else:
                return False



    def _fixheader(self):
        """ put some rubbish in to allow writing"""
        self.header['Dim_2'], self.header['Dim_1'] = self.data.shape
        self.bpp = len(self.data[0, 0].tostring())
        self.header['Size'] = len(self.data.tostring())
        for k in MINIMUM_KEYS:
            if k not in self.header:
                self.header[k] = DEFAULT_VALUES[k]


    def write(self, fname, force_type=np.uint16):
        """
        Try to write a file
        check we can write zipped also
        mimics that fabian was writing uint16 (we sometimes want floats)
        """
        self._fixheader()
        # Fabian was forcing uint16 - make this a default
        if force_type is not None:
            data = self.data.astype(force_type)
        else:
            data = self.data
        # Update header values to match the function local data object
        bpp = len(data[0, 0].tostring())
        if bpp not in [1, 2, 4]:
            logging.info("edfimage.write do you really want" + str(bpp) + \
                             "bytes per pixel??")
        bytecode = data.dtype.type
        for name , code in DATA_TYPES.items():
            if code == bytecode:
                self.header['DataType'] = name
                break
        dim2, dim1 = data.shape
        self.header['Dim_1'] = dim1
        self.header['Dim_2'] = dim2
        self.header['Size'] = dim1 * dim2 * bpp
        # checks for consistency:
        if bpp != self.bpp :
            logging.debug("Array upcasted? now " + str(bpp) + " was " + str(self.bpp))
        if dim1 != self.dim1 or dim2 != self.dim2 :
            logging.debug("corrupted image dimensions")
        outfile = self._open(fname, mode="wb")
        outfile.write('{\n') # Header start
        i = 4          # 2 so far, 2 to come at the end
        for k in self.header_keys:
            # We remove the extra whitespace on the key names to
            # avoiding making headers greater then 4 kb unless they already
            # were too big
            out = (("%-14s = %s ;\n") % (k, self.header[k]))
            i = i + len(out)
            outfile.write(out)
        # if additional items in the header just write them out in the
        # order they happen to be in
        for key, val in self.header.iteritems():
            if key in self.header_keys:
                continue
            out = (("%s = %s;\n") % (key, val))
            i = i + len(out)
            outfile.write(out)
        if i < 4096:
            out = (4096 - i) * ' '
        else:
            out = (1024 - i % 1024) * ' '  # Should make a total
            logging.warning("EDF Header is greater than 4096 bytes")
        outfile.write(out)
        i = i + len(out)
        assert i % 1024 == 0
        outfile.write('}\n')
        # print "Byteswapping?",
        if self.swap_needed():
            # print "did a swap"
            # data has "astype" from start of this function
            outfile.write(data.byteswap().tostring())
        else:
            # print "did not"
            outfile.write(data.tostring())
        outfile.close()
