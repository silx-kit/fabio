#!/usr/bin/env python
"""
Authors: Henning O. Sorensen & Erik Knudsen
         Center for Fundamental Research: Metal Structures in Four Dimensions
         Risoe National Laboratory
         Frederiksborgvej 399
         DK-4000 Roskilde
         email:erik.knudsen@risoe.dk

        + Jon Wright, ESRF
        + Jerome Kieffer, ESRF
"""

import numpy as np, logging
from fabio.fabioimage import fabioimage
import gzip, bz2, zlib, os, StringIO


BLOCKSIZE = 512
DATA_TYPES = {  "SignedByte"    :  np.int8,
                "Signed8"       :  np.int8,
                "UnsignedByte"  :  np.uint8,
                "Unsigned8"     :  np.uint8,
                "SignedShort"   :  np.int16,
                "Signed16"      :  np.int16,
                "UnsignedShort" :  np.uint16,
                "Unsigned16"    :  np.uint16,
                "UnsignedShortInteger" : np.uint16,
                "SignedInteger" :  np.int32,
                "Signed32"      :  np.int32,
                "UnsignedInteger":  np.uint32,
                "Unsigned32"    :  np.uint32,
                "SignedLong"    :  np.int32,
                "UnsignedLong"  :  np.uint32,
                "Signed64"      :  np.int64,
                "Unsigned64"    :  np.uint64,
                "FloatValue"    :  np.float32,
                "FLOATVALUE"    :  np.float32,
                "FLOAT"         :  np.float32, # fit2d
                "Float"         :  np.float32, # fit2d
                "FloatIEEE32"   :  np.float32,
                "DoubleValue"   :  np.float64,
                "FloatIEEE32"   :  np.float64
                }

COMPRESSION_SCHEME = ("None", "ZCompression", "GZCompression")

MINIMUM_KEYS = ['HEADERID',
                'IMAGE',
                'BYTEORDER',
                'DATATYPE',
                'DIM_1',
                'DIM_2',
                'SIZE'] # Size is thought to be essential for writing at least

DEFAULT_VALUES = {"HeaderID":  "EH:000001:000000:000000",
                  "Image":   "1",
                  "ByteOrder":  "LowByteFirst", # FIXME?
                  "DataType": "FLOAT"
                  }

STATIC_HEADER_ELEMENTS = ("HeaderID", "Image", "ByteOrder", "DataType",
                        "Dim_1", "Dim_2", "Dim_3",
                        "Offset_1", "Offset_2", "Offset_3",
                        "Size")
STATIC_HEADER_ELEMENTS_CAPS = ("HEADERID", "IMAGE", "BYTEORDER", "DATATYPE",
                             "DIM_1", "DIM_2", "DIM_3",
                             "OFFSET_1", "OFFSET_2", "OFFSET_3",
                             "SIZE")


class edfimage(fabioimage):
    """ Read and try to write the ESRF edf data format """

    def __init__(self, data=None , header=None):
        fabioimage.__init__(self, data, header)
        #Dictionary containing the header-KEY -> header-Key as EDF keys are supposed to be key insensitive
        self.dictCapsHeader = {}
        self.framesCapsHeader = []
        self.framesHeaders = []
        self.framesRawData = []
        self.framesData = []
        self.framesListHeader = []
        self.framesDims = []
        self.framesSize = []
        self.framesBpp = []


    def _readHeaderBlock(self, infile):
        """
        Read in a header in some EDF format from an already open file
        
        @param infile: file object open in read mode
        @return: string (or None if no header was found. 
        """

        block = infile.read(BLOCKSIZE)
        if len(block) < BLOCKSIZE:
            return
        if block[:4].find("{") < 0 :
            # This does not look like an edf file
            logging.warning("no opening {. Corrupt header of EDF file " + \
                            str(infile.name))
            return
        while '}' not in block:
            block = block + infile.read(BLOCKSIZE)
            if len(block) > BLOCKSIZE * 20:
                logging.warning("Runaway header in EDF file")
                return
        start = block.find("{") + 1
        end = block.find("}")

        # Now it is essential to go to the start of the binary part
        if block[end: end + 3] == "}\r\n":
            offset = end + 3 - len(block)
        elif block[end: end + 2] == "}\n":
            offset = end + 2 - len(block)
        else:
            logging.error("Unable to locate start of the binary section")
            offset = None
        if offset is not None:
            infile.seek(offset, os.SEEK_CUR)
        return block[start:end]


    def _parseheader(self, block):
        """
        Parse the header in some EDF format from an already open file

        @param block: string representing the header block
        @type block: string, should be full ascii
        @return: size of the binary blob
        """
        header = {}
        dictCapsHeader = {}
        header_keys = []
        for line in block.split(';'):
            if '=' in line:
                key, val = line.split('=' , 1)
                key = key.strip()
                header[key] = val.strip()
                dictCapsHeader[key.upper()] = key
                header_keys.append(key)
        self.framesCapsHeader.append(dictCapsHeader)
        self.framesHeaders.append(header)
        self.framesListHeader.append(header_keys)

        # Compute image size
        size = None
        calcsize = 1
        listDims = []
        if "SIZE" in dictCapsHeader:
            try:
                size = int(header[dictCapsHeader["SIZE"]])
            except ValueError:
                logging.warning("Unable to convert to integer : %s %s " % (dictCapsHeader["SIZE"], header[dictCapsHeader["SIZE"]]))
        if "DIM_1" in dictCapsHeader:
            try:
                dim1 = int(header[dictCapsHeader['DIM_1']])
            except ValueError:
                logging.error("Unable to convert to integer Dim_1: %s %s"(dictCapsHeader["DIM_1"], header[dictCapsHeader["DIM_1"]]))
            else:
                calcsize *= dim1
                listDims.append(dim1)
        else:
            logging.error("No Dim_1 in headers !!!")
        if "DIM_2" in dictCapsHeader:
            try:
                dim2 = int(header[dictCapsHeader['DIM_2']])
            except ValueError:
                logging.error("Unable to convert to integer Dim_3: %s %s"(dictCapsHeader["DIM_2"], header[dictCapsHeader["DIM_2"]]))
            else:
                calcsize *= dim2
                listDims.append(dim2)
        else:
            logging.error("No Dim_2 in headers !!!")
        iDim = 3
        while iDim is not None:
            strDim = "DIM_%i" % iDim
            if strDim in dictCapsHeader:
                try:
                    dim3 = int(header[dictCapsHeader[strDim]])
                except ValueError:
                    logging.error("Unable to convert to integer %s: %s %s"
                                  % (strDim, dictCapsHeader[strDim], header[dictCapsHeader[strDim]]))
                    dim3 = None
                    iDim = None
                else:
                    calcsize *= dim3
                    listDims.append(dim3)
                    iDim += 1
            else:
                logging.debug("No Dim_3 -> it is a 2D image")
                iDim = None

        if "DATATYPE" in dictCapsHeader:
            bytecode = DATA_TYPES[header[dictCapsHeader['DATATYPE']]]
        else:
            bytecode = np.uint16
            logging.warning("Defaulting type to uint16")
        bpp = len(np.array(0, bytecode).tostring())
        calcsize *= bpp
        if (size is None):
            size = calcsize
        elif (size != calcsize):
            if ("COMPRESSION" in dictCapsHeader) and (header[dictCapsHeader['COMPRESSION']].upper().startswith("NO")):
                logging.error("Mismatch between the expected size %s and the calculated one %s" % (size, calcsize))
        self.framesBpp.append(bpp)
        self.framesDims.append(listDims)
        self.framesSize.append(size)
        return size


    def _readheader(self, infile):
        """
        Read all headers in a file and populate self.header
        data is not yet populated
        """

        bContinue = True
        while bContinue:
            block = self._readHeaderBlock(infile)
            if block is None:
                bContinue = False
                break
            size = self._parseheader(block)
            datablock = infile.read(size)
            if len(datablock) != size:
                logging.warning("Non complete datablock: got %s, expected %s" % (len(datablock), size))
                bContinue = False
                break
            self.framesRawData.append(datablock)
#            On the fly image decompression
            self.framesData.append(None)

        for frame, dictFrameCapsHeader in enumerate(self.framesCapsHeader):
            missing = []
            for item in MINIMUM_KEYS:
                if item not in dictFrameCapsHeader:
                    missing.append(item)
            if len(missing) > 0:
                logging.warning("EDF file %s frame %i misses mandatory keys: %s " % (self.filename, frame, " ".join(missing)))


        self.currentframe = 0
        self.header = self.framesHeaders[0]
        self.dictCapsHeader = self.framesCapsHeader[0]
        self.header_keys = self.framesListHeader[0]
        self.nframes = len(self.framesListHeader)
        for i, n in enumerate(self.framesDims[0]):
            exec "self.dim%i=%i" % (i + 1, n)
        self.bpp = self.framesBpp[0]


    def read(self, fname):
        """
        Read in header into self.header and
            the data   into self.data
        """
        self.header = {}
        self.dictCapsHeader = {}
        self.framesCapsHeader = []
        self.framesHeaders = []
        self.framesRawData = []
        self.framesData = []
        self.framesListHeader = []
        self.framesDims = []
        self.framesSize = []
        self.framesBpp = []
        self.resetvals()
        self.filename = fname
        infile = self._open(fname, "rb")
        self._readheader(infile)
        if self.data is None:
            data = self.unpack()
            self.framesData[0] = data
            self.bytecode = data.dtype.type
        self.resetvals()
        # ensure the PIL image is reset
        self.pilimage = None
        return self

    def swap_needed(self):
        """
        Decide if we need to byteswap
        """
        if ('Low'  in self.header[self.dictCapsHeader['BYTEORDER']] and np.little_endian) or \
           ('High' in self.header[self.dictCapsHeader['BYTEORDER']] and not np.little_endian):
            return False
        if ('High'  in self.header[self.dictCapsHeader['BYTEORDER']] and np.little_endian) or \
           ('Low' in self.header[self.dictCapsHeader['BYTEORDER']] and not np.little_endian):
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

    def unpack(self):
        """
        Unpack a binary blob according to the specification given in the header

        @return: dataset as numpy.ndarray
        """

        if "DATATYPE" in self.dictCapsHeader:
            bytecode = DATA_TYPES[self.header[self.dictCapsHeader["DATATYPE"]]]
        else:
            bytecode = np.uint16
        dims = self.framesDims[self.currentframe]
        dims.reverse()
        size = 1
        for i in dims:
            size *= i
        bpp = len(np.array(0, dtype=bytecode).tostring())

        if ("COMPRESSION" in self.dictCapsHeader):
            compression = self.header[self.dictCapsHeader["COMPRESSION"]].upper()
            if "OFFSET" in compression :
                try:
                    import byte_offset
                except ImportError:
                    logging.error("Unimplemented compression scheme:  %s" % compression)
                else:
                    myData = byte_offset.analyseCython(self.framesRawData[self.currentframe], size=size)
                    rawData = myData.astype(bytecode).tostring()
            elif compression == "NONE":
                rawData = self.framesRawData[self.currentframe]
            elif "GZIP" in compression:
                fileobj = StringIO.StringIO(self.framesRawData[self.currentframe])
                try:
                    rawData = gzip.GzipFile(fileobj=fileobj).read()
                except IOError:
                    logging.warning("Encounter the python-gzip bug with trailing garbage")
                    #This is as an ugly hack against a bug in Python gzip
                    import subprocess
                    sub = subprocess.Popen(["gzip", "-d", "-f"], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
                    rawData, err = sub.communicate(input=self.framesRawData[self.currentframe])
                    logging.debug("Gzip subprocess ended with %s err= %s; I got %s bytes back" % (sub.wait(), err, len(rawData)))
            elif "BZ" in compression :
                rawData = bz2.decompress(self.framesRawData[self.currentframe])
            elif "Z" in compression :
                rawData = zlib.decompress(self.framesRawData[self.currentframe])
            else:
                logging.warning("Unknown compression scheme %s" % compression)
                rawData = self.framesRawData[self.currentframe]
        else:
                rawData = self.framesRawData[self.currentframe]

        expected = bpp * size
        obtained = len(rawData)
        if expected > obtained:
            logging.error("Compressed data stream is incomplete: %s < expected %s bytes" % (obtained, expected))
            rawData += "\x00" * (expected - obtained)
        elif expected < len(rawData):
            logging.warning("Compressed data stream contains trailing junk : %s > expected %s bytes" % (obtained, expected))
            rawData = rawData[:expected]
        if self.swap_needed():
            data = np.fromstring(rawData, bytecode).byteswap().reshape(tuple(dims))
        else:
            data = np.fromstring(rawData, bytecode).reshape(tuple(dims))
        self.data = data
        self.bytecode = data.dtype.type
        self.resetvals()
        self.pilimage = None
        return data


    def getframe(self, num):
        """ returns the file numbered 'num' in the series as a fabioimage """
        if num in xrange(self.nframes):
#            rawData = self.framesRawData[num]
            header = self.framesHeaders[num]
            dictCaps = self.framesCapsHeader[num]
            newImage = edfimage(data=self.framesData[num], header=header)
            newImage.dictCapsHeader = dictCaps
            newImage.header_keys = self.framesListHeader[num]
            newImage.nframes = self.nframes
            newImage.currentframe = num
            newImage.filename = self.filename
            newImage.framesRawData = self.framesRawData
            newImage.framesData = self.framesData
            newImage.framesHeaders = self.framesHeaders
            newImage.framesListHeader = self.framesListHeader
            newImage.framesDims = self.framesDims
            newImage.dim1, newImage.dim2 = tuple(newImage.framesDims[num][:2])
            newImage.framesSize = self.framesSize
            if newImage.data is None:
                data = newImage.unpack()
                self.framesData[num] = data
            return newImage
        else:
            logging.error("Cannot access frame: %s" % num)
            raise ValueError("edfimage.getframe: index out of range: %s" % num)



    def previous(self):
        """ returns the previous file in the series as a fabioimage """
        if self.nframes == 1:
            return fabioimage.previous(self)
        else:
            newFrameId = self.currentframe - 1
            return self.getframe(newFrameId)


    def next(self):
        """ returns the next file in the series as a fabioimage """
        if self.nframes == 1:
            return fabioimage.previous(self)
        else:
            newFrameId = self.currentframe + 1
            return self.getframe(newFrameId)


    def write(self, fname, force_type=None):
        """
        Try to write a file
        check we can write zipped also
        mimics that fabian was writing uint16 (we sometimes want floats)
        
        @param force_type: can be numpy.uint16 or simply "float"
        @return: None
        
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
