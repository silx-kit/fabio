#!/usr/bin/env python
# -*- coding: utf8 -*-
"""

License: GPLv2+

Authors: Henning O. Sorensen & Erik Knudsen
         Center for Fundamental Research: Metal Structures in Four Dimensions
         Risoe National Laboratory
         Frederiksborgvej 399
         DK-4000 Roskilde
         email:erik.knudsen@risoe.dk

        + Jon Wright, ESRF
        
2011-02-11: Mostly rewritten by Jérôme Kieffer (Jerome.Kieffer@esrf.eu) 
            European Synchrotron Radiation Facility
            Grenoble (France)

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
                "Float32"       :  np.float32,
                "DoubleValue"   :  np.float64,
                "FloatIEEE64"   :  np.float64,
                "DoubleIEEE64"  :  np.float64
                }

NUMPY_EDF_DTYPE = {"int8"       :"Signed8",
                   "int16"      :"Signed16",
                   "int32"      :"Signed32",
                   "int64"      :"Signed64",
                   "uint8"      :"Unsigned8",
                   "uint16"     :"Unsigned16",
                   "uint32"     :"Unsigned32",
                   "uint64"     :"Unsigned64",
                   "float32"    :"FloatIEEE32",
                   "float64"    :"DoubleIEEE64"
             }

MINIMUM_KEYS = ['HEADERID',
                'IMAGE',
                'BYTEORDER',
                'DATATYPE',
                'DIM_1',
                'DIM_2',
                'SIZE'] # Size is thought to be essential for writing at least



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

    @staticmethod
    def _readHeaderBlock(infile):
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
                logging.error("Unable to convert to integer Dim_1: %s %s" % (dictCapsHeader["DIM_1"], header[dictCapsHeader["DIM_1"]]))
            else:
                calcsize *= dim1
                listDims.append(dim1)
        else:
            logging.error("No Dim_1 in headers !!!")
        if "DIM_2" in dictCapsHeader:
            try:
                dim2 = int(header[dictCapsHeader['DIM_2']])
            except ValueError:
                logging.error("Unable to convert to integer Dim_3: %s %s" % (dictCapsHeader["DIM_2"], header[dictCapsHeader["DIM_2"]]))
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
            logging.error("Data stream is incomplete: %s < expected %s bytes" % (obtained, expected))
            rawData += "\x00" * (expected - obtained)
        elif expected < len(rawData):
            logging.warning("Data stream contains trailing junk : %s > expected %s bytes" % (obtained, expected))
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
        frame = 0
        outfile = self._open(fname, mode="wb")
        for header, header_keys, data, capsHeader in zip(self.framesHeaders, self.framesListHeader, self.framesData, self.framesCapsHeader):
            if data is None:
                data = self.getframe(frame).data
            frame += 1
            if force_type is not None:
                data = data.astype(force_type)
            listHeader = ["{\n"]
#        First of all clean up the headers:
            for i in capsHeader:
                if "DIM_" in i:
                    header.pop(capsHeader[i])
                    header_keys.remove(capsHeader[i])
            for KEY in ["SIZE", "EDF_DATABLOCKID", "EDF_BINARYSIZE", "EDF_HEADERSIZE", "BYTEORDER", "DATATYPE", "HEADERID", "IMAGE"]:
                if KEY in capsHeader:
                    header.pop(capsHeader[KEY])
                    header_keys.remove(capsHeader[KEY])
#            Then update static headers freshly deleted
            header_keys.insert(0, "Size")
            header["Size"] = len(data.tostring())
            header_keys.insert(0, "HeaderID")
            header["HeaderID"] = "EH:%06d:000000:000000" % frame
            header_keys.insert(0, "Image")
            header["Image"] = str(frame)

            dims = list(data.shape)
            nbdim = len(dims)
            for i in dims:
                key = "Dim_%i" % nbdim
                header[key] = i
                header_keys.insert(0, key)
                nbdim -= 1
            header_keys.insert(0, "DataType")
            header["DataType"] = NUMPY_EDF_DTYPE[str(np.dtype(data.dtype))]
            header_keys.insert(0, "ByteOrder")
            if np.little_endian:
                header["ByteOrder"] = "LowByteFirst"
            else:
                header["ByteOrder"] = "HighByteFirst"
            approxHeaderSize = 100
            for key in header:
                approxHeaderSize += 7 + len(key) + len(str(header[key]))
            approxHeaderSize = BLOCKSIZE * (approxHeaderSize // BLOCKSIZE + 1)
            header_keys.insert(0, "EDF_HeaderSize")
            header["EDF_HeaderSize"] = str(BLOCKSIZE * (approxHeaderSize // BLOCKSIZE + 1))
            header_keys.insert(0, "EDF_BinarySize")
            header["EDF_BinarySize"] = len(data.tostring())
            header_keys.insert(0, "EDF_DataBlockID")
            header["EDF_DataBlockID"] = "%i.Image.Psd" % frame
            preciseSize = 4 #2 before {\n 2 after }\n
            for key in header_keys:
                line = "%s = %s ;\n" % (key, header[key])
                preciseSize += len(line)
                listHeader.append(line)
            if preciseSize > approxHeaderSize:
                logging.error("I expected the header block only at %s in fact it is %s" % (approxHeaderSize, preciseSize))
                for  idx, line in enumerate(listHeader[:]):
                    if line.startswith("EDF_HeaderSize"):
                        headerSize = BLOCKSIZE * (preciseSize // BLOCKSIZE + 1)
                        newline = "EDF_HeaderSize = %s ;\n" % headerSize
                        delta = len(newline) - len(line)
                        if (preciseSize // BLOCKSIZE) != ((preciseSize + delta) // BLOCKSIZE):
                            headerSize = BLOCKSIZE * ((preciseSize + delta) // BLOCKSIZE + 1)
                            newline = "EDF_HeaderSize = %s ;\n" % headerSize
                        preciseSize = preciseSize + delta
                        listHeader[idx] = newline
                        break
            else:
                headerSize = approxHeaderSize
            listHeader.append(" "*(headerSize - preciseSize) + "}\n")
            outfile.writelines(listHeader)
            outfile.write(data.tostring())
        outfile.close()
