## Automatically adapted for numpy.oldnumeric Oct 05, 2007 by alter_code1.py

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

import numpy.oldnumeric as Numeric, logging

from fabio.fabioimage import fabioimage


DATA_TYPES = {  "SignedByte"     :  Numeric.Int8,
                "UnsignedByte"   :  Numeric.UInt8,
                "SignedShort"    :  Numeric.Int16,
                "UnsignedShort"  :  Numeric.UInt16,
                "UnsignedShortInteger" : Numeric.UInt16,
                "SignedInteger"  :  Numeric.Int32,
                "UnsignedInteger":  Numeric.UInt32,
                "SignedLong"     :  Numeric.Int,
                "UnsignedLong"   :  Numeric.UInt,
                "FloatValue"     :  Numeric.Float32,
                "FLOAT"          :  Numeric.Float32, # fit2d
                "DoubleValue"    :  Numeric.Float
                }

MINIMUM_KEYS = ['HeaderID',
                'Image',
                'ByteOrder',
                'DataType',
                'Dim_1',
                'Dim_2']

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
        block = infile.read(1024)
        if block[:4].find("{") < 0 :
            # This does not look like an edf file
            logging.warning("no opening {. Corrupt header of EDF file " + \
                            str(infile.name))

        while '}' not in block:
            block = block + infile.read(1024)
            if len(block) > 1024*20:
                raise Exception("Runaway header in EDF file")
        start , end = block.find("{")+1, block.find("}")
        for line in block[start:end].split(';'):
            if '=' in line:
                key, val = line.split( '=' , 1)
                # Users cannot type in significant whitespace
                key = key.rstrip().lstrip()
                self.header_keys.append(key)
                self.header[key] = val.lstrip().rstrip()
        missing = []
        for item in MINIMUM_KEYS:
            if item not in self.header_keys:
                missing.append(item)
        if len(missing)>0:
            logging.debug("EDF file misses the keys "+" ".join(missing))

    def read(self, fname):
        """
        Read in header into self.header and
            the data   into self.data
        """
        self.header = {}
        self.resetvals()
        infile = self._open(fname)
        self._readheader(infile)
        # Compute image size
        try:
            self.dim1 = int(self.header['Dim_1'])
            self.dim2 = int(self.header['Dim_2'])
        except:
            raise Exception("EDF file", str(fname) + \
                                "is corrupt, cannot read it")
        try:
            bytecode  = DATA_TYPES[self.header['DataType']]
        except KeyError:
            bytecode = Numeric.UInt16
            logging.warning("Defaulting type to UInt16")
        self.bpp = len(Numeric.array(0, bytecode).tostring())

        if self.header.has_key("Size"): # fit2d does not write this
            if self.bpp*self.dim1*self.dim2 != int(self.header["Size"]):
                logging.warning("Size mismatch on reading edf file " + \
                                    fname + " " + self.header["Size"])
        # Sorry - this was the only safe way to read old ID11 imagepro edfs
        if self.header.has_key('Image') and self.header['Image'] == '1':
            block = infile.read()
        else:
            # oh dear
            raise Exception("Could be a multi-image file")
        expected_size =  self.dim1 * self.dim2 * self.bpp
        if len(block) != expected_size:
            # probably header overspill
            logging.warning("Read too many bytes, got "+str(len(block))+\
                                " want "+ str(expected_size))
            block = block[-expected_size:]
        if len(block) < expected_size:
            # FIXME
            logging.warning("Padded")
        infile.close()

        #now read the data into the array
        try:
            self.data = Numeric.reshape(
                Numeric.fromstring(block, bytecode ),
                [self.dim2, self.dim1])
        except:
            print len(block), bytecode, self.bpp, self.dim2, self.dim1
            raise IOError, \
              'Size spec in edf-header does not match size of image data field'
        self.bytecode = self.data.dtype.char
        swap = self.swap_needed()
        if swap:
            self.data = self.data.byteswap()
            # Remove verbose arg - use logging and levels
            logging.info('Byteswapped from '+self.header['ByteOrder'])
        else:
            logging.info('using '+self.header['ByteOrder'])
        self.resetvals()
        # ensure the PIL image is reset
        self.pilimage = None
        return self

    def swap_needed(self ):
        """
        Decide if we need to byteswap
        """
        if ('Low'  in self.header['ByteOrder'] and Numeric.LittleEndian ) or \
           ('High' in self.header['ByteOrder'] and not Numeric.LittleEndian ):
            return False
        if ('High'  in self.header['ByteOrder'] and Numeric.LittleEndian ) or \
           ('Low' in self.header['ByteOrder'] and not Numeric.LittleEndian ):
            if self.bpp in [2, 4, 8]:
                return True
            else:
                return False



    def write(self, fname, force_type = Numeric.UInt16 ):
        """
        Try to write a file
        check we can write zipped also
        mimics that fabian was writing UInt16 (we sometimes want floats)
        """
        # Fabian was forcing UInt16 - make this a default
        if force_type is not None:
            data = self.data.astype(force_type)
        else:
            data = self.data
        # Update header values to match the function local data object
        bpp = len( data[0, 0].tostring() )
        if bpp not in [1, 2, 4]:
            logging.info("edfimage.write do you really want"+str(bpp)+\
                             "bytes per pixel??")
        bytecode = data.dtype.char
        for name , code in DATA_TYPES.items():
            if code == bytecode:
                self.header['DataType'] = name
                break
        dim2, dim1 = data.shape
        self.header['Dim_1'] = dim1
        self.header['Dim_2'] = dim2
        self.header['Size'] = dim1*dim2*bpp
        # checks for consistency:
        if bpp != self.bpp :
            logging.debug("Array upcasted? now "+str(bpp)+" was "+str(self.bpp))
        if dim1 != self.dim1 or dim2 != self.dim2 :
            logging.debug("corrupted image dimensions")
        outfile = self._open(fname, mode="wb")
        outfile.write('{\n') # Header start
        i = 4          # 2 so far, 2 to come at the end
        for k in self.header_keys:
            out = (("%s = %s;\n") % (k, self.header[k]))
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
            out = (4096-i)*' '
        else:
            out = (1024 - i%1024)*' '  # Should make a total
            logging.warning("EDF Header is greater than 4096 bytes")
        outfile.write(out)
        i = i + len(out)
        assert i % 1024 == 0
        outfile.write('}\n')
        if self.swap_needed():
            # data has "astype" from start of this function
            outfile.write(data.byteswap().tostring())
        else:
            outfile.write(data.tostring())
        outfile.close()
