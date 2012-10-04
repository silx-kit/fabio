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
2012-08-20: laisy read of data in EDF
"""
from __future__ import with_statement
import os, logging, types
logger = logging.getLogger("edfimage")
import numpy
from fabioimage import fabioimage
from fabioutils import isAscii, toAscii, nice_int
from compression import decBzip2, decGzip, decZlib


BLOCKSIZE = 512
DATA_TYPES = {  "SignedByte"    :  numpy.int8,
                "Signed8"       :  numpy.int8,
                "UnsignedByte"  :  numpy.uint8,
                "Unsigned8"     :  numpy.uint8,
                "SignedShort"   :  numpy.int16,
                "Signed16"      :  numpy.int16,
                "UnsignedShort" :  numpy.uint16,
                "Unsigned16"    :  numpy.uint16,
                "UnsignedShortInteger" : numpy.uint16,
                "SignedInteger" :  numpy.int32,
                "Signed32"      :  numpy.int32,
                "UnsignedInteger":  numpy.uint32,
                "Unsigned32"    :  numpy.uint32,
                "SignedLong"    :  numpy.int32,
                "UnsignedLong"  :  numpy.uint32,
                "Signed64"      :  numpy.int64,
                "Unsigned64"    :  numpy.uint64,
                "FloatValue"    :  numpy.float32,
                "FLOATVALUE"    :  numpy.float32,
                "FLOAT"         :  numpy.float32, # fit2d
                "Float"         :  numpy.float32, # fit2d
                "FloatIEEE32"   :  numpy.float32,
                "Float32"       :  numpy.float32,
                "Double"        :  numpy.float64,
                "DoubleValue"   :  numpy.float64,
                "FloatIEEE64"   :  numpy.float64,
                "DoubleIEEE64"  :  numpy.float64}
try:
    DATA_TYPES["FloatIEEE128" ] =  numpy.float128
    DATA_TYPES["DoubleIEEE128" ] =  numpy.float128
    DATA_TYPES["QuadrupleValue" ] =  numpy.float128

except AttributeError:
    # not in your numpy
    pass

NUMPY_EDF_DTYPE = {"int8"       :"SignedByte",
                   "int16"      :"SignedShort",
                   "int32"      :"SignedInteger",
                   "int64"      :"Signed64",
                   "uint8"      :"UnsignedByte",
                   "uint16"     :"UnsignedShort",
                   "uint32"     :"UnsignedInteger",
                   "uint64"     :"Unsigned64",
                   "float32"    :"FloatValue",
                   "float64"    :"DoubleValue",
                   "float128"   :"QuadrupleValue",
             }

MINIMUM_KEYS = ['HEADERID',
                'IMAGE',
                'BYTEORDER',
                'DATATYPE',
                'DIM_1',
                'DIM_2',
                'SIZE'] # Size is thought to be essential for writing at least

DEFAULT_VALUES = {
                  # I do not define default values as they will be calculated at write time
                  # JK20110415
                  }

class Frame(object):
    """
    A class representing a single frame in an EDF file
    """
    def __init__(self, data=None, header=None, header_keys=None, number=None):
        if header is None:
            self.header = {}
        else:
            self.header = dict(header)

        if header_keys is None:
            self.header_keys = self.header.keys()
        else:
            self.header_keys = header_keys[:]
            for key in header_keys:
                if key not in self.header:
                    logger.warning("Header key %s, in header_keys is not in header dictionary, poping !!!" % key)
                    self.header_keys.remove(key)

        self.capsHeader = {}
        for key in self.header_keys:
            try:
                self.capsHeader[key.upper()] = key
            except AttributeError:
                logger.warning("Header key %s is not a string" % key)
        self._data = data
        self.dims = []
        self.dim1 = 0
        self.dim2 = 0
        self.start = None # Position of start of raw data in file
        self.size = None  # size of raw data in file
        self.file = None  # opened file object with locking capabilities !!!
        self.bpp = None
        self._bytecode = None
        if (number is not None) and isinstance(number, int):
            self.iFrame = number
        else:
            self.iFrame = 0

    def parseheader(self, block):
        """
        Parse the header in some EDF format from an already open file

        @param block: string representing the header block
        @type block: string, should be full ascii
        @return: size of the binary blob
        """
        #reset values ...
        self.header = {}
        self.capsHeader = {}
        self.header_keys = []
        self.size = None
        calcsize = 1
        self.dims = []

        for line in block.split(';'):
            if '=' in line:
                key, val = line.split('=' , 1)
                # Why would someone put null bytes in a header?
                key = key.replace("\x00"," ").strip()
                self.header[key] = val.replace("\x00"," ").strip()
                self.capsHeader[key.upper()] = key
                self.header_keys.append(key)

        # Compute image size
        if "SIZE" in self.capsHeader:
            try:
                self.size = nice_int(self.header[self.capsHeader["SIZE"]])
            except ValueError:
                logger.warning("Unable to convert to integer : %s %s " % (self.capsHeader["SIZE"], self.header[self.capsHeader["SIZE"]]))
        if "DIM_1" in self.capsHeader:
            try:
                dim1 = nice_int(self.header[self.capsHeader['DIM_1']])
            except ValueError:
                logger.error("Unable to convert to integer Dim_1: %s %s" % (self.capsHeader["DIM_1"], self.header[self.capsHeader["DIM_1"]]))
            else:
                calcsize *= dim1
                self.dims.append(dim1)
        else:
            logger.error("No Dim_1 in headers !!!")
        if "DIM_2" in self.capsHeader:
            try:
                dim2 = nice_int(self.header[self.capsHeader['DIM_2']])
            except ValueError:
                logger.error("Unable to convert to integer Dim_3: %s %s" % (self.capsHeader["DIM_2"], self.header[self.capsHeader["DIM_2"]]))
            else:
                calcsize *= dim2
                self.dims.append(dim2)
        else:
            logger.error("No Dim_2 in headers !!!")
        iDim = 3
        # JON: this appears to be for nD images, but we don't treat those
        while iDim is not None:
            strDim = "DIM_%i" % iDim
            if strDim in self.capsHeader:
                try:
                    dim3 = nice_int(self.header[self.capsHeader[strDim]])
                except ValueError:
                    logger.error("Unable to convert to integer %s: %s %s"
                                  % (strDim, self.capsHeader[strDim], self.header[self.capsHeader[strDim]]))
                    dim3 = None
                    iDim = None
                else:
                    if dim3 > 1:
                        # Otherwise treat dim3==1 as a 2D image
                        calcsize *= dim3
                        self.dims.append(dim3)
                    iDim += 1

            else:
                logger.debug("No Dim_3 -> it is a 2D image")
                iDim = None
        if self._bytecode is None:
            if "DATATYPE" in self.capsHeader:
                self._bytecode = DATA_TYPES[self.header[self.capsHeader['DATATYPE']]]
            else:
                self._bytecode = numpy.uint16
                logger.warning("Defaulting type to uint16")
        self.bpp = len(numpy.array(0, self._bytecode).tostring())
        calcsize *= self.bpp
        if (self.size is None):
            self.size = calcsize
        elif (self.size != calcsize):
            if ("COMPRESSION" in self.capsHeader) and (self.header[self.capsHeader['COMPRESSION']].upper().startswith("NO")):
                logger.info("Mismatch between the expected size %s and the calculated one %s" % (self.size, calcsize))
                self.size = calcsize

        for i, n in enumerate(self.dims):
            setattr(self, "dim%i" % (i + 1), n)

        return self.size


    def swap_needed(self):
        """
        Decide if we need to byteswap
        """
        if ('Low'  in self.header[self.capsHeader['BYTEORDER']] and numpy.little_endian) or \
           ('High' in self.header[self.capsHeader['BYTEORDER']] and not numpy.little_endian):
            return False
        if ('High'  in self.header[self.capsHeader['BYTEORDER']] and numpy.little_endian) or \
           ('Low' in self.header[self.capsHeader['BYTEORDER']] and not numpy.little_endian):
            if self.bpp in [2, 4, 8]:
                return True
            else:
                return False


    def getData(self):
        """
        Unpack a binary blob according to the specification given in the header

        @return: dataset as numpy.ndarray
        """
        data = None
        if self._data is not None:
            data = self._data
        elif self.file is None:
            data = self._data
        else:
            if self._bytecode is None:
                if "DATATYPE" in self.capsHeader:
                    self._bytecode = DATA_TYPES[self.header[self.capsHeader["DATATYPE"]]]
                else:
                    self._bytecode = numpy.uint16
            dims = self.dims[:]
            dims.reverse()
            with self.file.lock:
                if self.file.closed:
                    logger.error("file: %s from %s is closed. Cannot read data." % (self.file, self.file.filename))
                    return
                else:
                    self.file.seek(self.start)
                    fileData = self.file.read(self.size)

            if ("COMPRESSION" in self.capsHeader):
                compression = self.header[self.capsHeader["COMPRESSION"]].upper()
                uncompressed_size = self.bpp
                for i in dims:
                    uncompressed_size *= i
                if "OFFSET" in compression :
                    try:
                        import byte_offset#IGNORE:F0401
                    except ImportError, error:
                        logger.error("Unimplemented compression scheme:  %s (%s)" % (compression, error))
                    else:
                        myData = byte_offset.analyseCython(fileData, size=uncompressed_size)
                        rawData = myData.astype(self._bytecode).tostring()
                        self.size = uncompressed_size
                elif compression == "NONE":
                    rawData = fileData
                elif "GZIP" in compression:
                    rawData = decGzip(fileData)
                    self.size = uncompressed_size
                elif "BZ" in compression :
                    rawData = decBzip2(fileData)
                    self.size = uncompressed_size
                elif "Z" in compression :
                    rawData = decZlib(fileData)
                    self.size = uncompressed_size
                else:
                    logger.warning("Unknown compression scheme %s" % compression)
                    rawData = fileData

            else:
                rawData = fileData

            expected = self.size
            obtained = len(rawData)
            if expected > obtained:
                logger.error("Data stream is incomplete: %s < expected %s bytes" % (obtained, expected))
                rawData += "\x00" * (expected - obtained)
            elif expected < len(rawData):
                logger.info("Data stream contains trailing junk : %s > expected %s bytes" % (obtained, expected))
                rawData = rawData[:expected]
            if self.swap_needed():
                data = numpy.fromstring(rawData, self._bytecode).byteswap().reshape(tuple(dims))
            else:
                data = numpy.fromstring(rawData, self._bytecode).reshape(tuple(dims))
            self._data = data
            self._bytecode = data.dtype.type
        return data
    def setData(self, npa=None):
        """Setter for data in edf frame"""
        self._data = npa
    data = property(getData, setData, "property: (edf)frame.data, uncompress the datablock when needed")
    def getByteCode(self):
        if self._bytecode is None:
            self._bytecode = self.data.dtype.type

        return self._bytecode
    def setByteCode(self, _iVal):
        self._bytecode = _iVal
    bytecode = property(getByteCode, setByteCode)

    def getEdfBlock(self, force_type=None, fit2dMode=False):
        """
        @param force_type: type of the dataset to be enforced like "float64" or "uint16"
        @type force_type: string or numpy.dtype
        @param fit2dMode: enforce compatibility with fit2d and starts countimg number of images at 1
        @type fit2dMode: boolean
        @return: ascii header block
        @rtype: python string with the concatenation of the ascii header and the binary data block
        """
        if force_type is not None:
            data = self.data.astype(force_type)
        else:
            data = self.data
        fit2dMode = bool(fit2dMode)
        for key in self.header:
            KEY = key.upper()
            if KEY not in self.capsHeader:
                self.capsHeader[KEY] = key
            if key not in self.header_keys:
                self.header_keys.append(key)

        header = self.header.copy()
        header_keys = self.header_keys[:]
        capsHeader = self.capsHeader.copy()

        listHeader = ["{\n"]
#        First of all clean up the headers:
        for i in capsHeader:
            if "DIM_" in i:
                header.pop(capsHeader[i])
                header_keys.remove(capsHeader[i])
        for KEY in ["SIZE", "EDF_BINARYSIZE", "EDF_HEADERSIZE", "BYTEORDER", "DATATYPE", "HEADERID", "IMAGE"]:
            if KEY in capsHeader:
                header.pop(capsHeader[KEY])
                header_keys.remove(capsHeader[KEY])
        if "EDF_DATABLOCKID" in capsHeader:
            header_keys.remove(capsHeader["EDF_DATABLOCKID"])
            #but do not remove the value from dict, instead reset the key ...
            if capsHeader["EDF_DATABLOCKID"] != "EDF_DataBlockID":
                header["EDF_DataBlockID"] = header.pop(capsHeader["EDF_DATABLOCKID"])
                capsHeader["EDF_DATABLOCKID"] = "EDF_DataBlockID"

#            Then update static headers freshly deleted
        header_keys.insert(0, "Size")
        header["Size"] = len(data.tostring())
        header_keys.insert(0, "HeaderID")
        header["HeaderID"] = "EH:%06d:000000:000000" % (self.iFrame + fit2dMode)
        header_keys.insert(0, "Image")
        header["Image"] = str(self.iFrame + fit2dMode)

        dims = list(data.shape)
        nbdim = len(dims)
        for i in dims:
            key = "Dim_%i" % nbdim
            header[key] = i
            header_keys.insert(0, key)
            nbdim -= 1
        header_keys.insert(0, "DataType")
        header["DataType"] = NUMPY_EDF_DTYPE[str(numpy.dtype(data.dtype))]
        header_keys.insert(0, "ByteOrder")
        if numpy.little_endian:
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
        if not "EDF_DataBlockID" in header:
            header["EDF_DataBlockID"] = "%i.Image.Psd" % (self.iFrame + fit2dMode)
        preciseSize = 4 #2 before {\n 2 after }\n
        for key in header_keys:
            #Escape keys or values that are no ascii
            strKey = str(key)
            if not isAscii(strKey, listExcluded=["}", "{"]):
                logger.warning("Non ascii key %s, skipping" % strKey)
                continue
            strValue = str(header[key])
            if not isAscii(strValue, listExcluded=["}", "{"]):
                logger.warning("Non ascii value %s, skipping" % strValue)
                continue
            line = strKey + " = " + strValue + " ;\n"
            preciseSize += len(line)
            listHeader.append(line)
        if preciseSize > approxHeaderSize:
            logger.error("I expected the header block only at %s in fact it is %s" % (approxHeaderSize, preciseSize))
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
        return "".join(listHeader) + data.tostring()



class edfimage(fabioimage):
    """ Read and try to write the ESRF edf data format """

    def __init__(self, data=None , header=None, header_keys=None, frames=None):
        self.currentframe = 0
        self.filesize = None
        try:
            dim = len(data.shape)
        except Exception, error: #IGNORE:W0703
            logger.debug("Data don't look like a numpy array (%s), resetting all!!" % error)
            data = None
            dim = 0
            fabioimage.__init__(self, data, header)
        if dim == 2:
            fabioimage.__init__(self, data, header)
        elif dim == 1 :
            data.shape = (0, len(data))
            fabioimage.__init__(self, data, header)
        elif dim == 3 :
            fabioimage.__init__(self, data[0, :, :], header)
        elif dim == 4 :
            fabioimage.__init__(self, data[0, 0, :, :], header)
        elif dim == 5 :
            fabioimage.__init__(self, data[0, 0, 0, :, :], header)

        if frames is None:
            frame = Frame(data=self.data, header=self.header,
                          header_keys=header_keys ,
                          number=self.currentframe)
            self.__frames = [frame]
        else:
            self.__frames = frames

    @staticmethod
    def checkHeader(header=None):
        """
        Empty for fabioimage but may be populated by others classes
        """
        if type(header) != types.DictionaryType:
            return {}
        new = {}
        for key, value in header.items():
            new[toAscii(key, ";{}")] = toAscii(value, ";{}")
        return new

    @staticmethod
    def _readHeaderBlock(infile):
        """
        Read in a header in some EDF format from an already open file

        @param infile: file object open in read mode
        @return: string (or None if no header was found.
        """

        block = infile.read(BLOCKSIZE)
        if len(block) < BLOCKSIZE:
            logger.debug("Under-short header: only %i bytes in %s" % (len(block), infile.name))
            return
        if (block.find("{") < 0) :
            # This does not look like an edf file
            logger.warning("no opening {. Corrupt header of EDF file %s" % infile.name)
            return
        while '}' not in block:
            block = block + infile.read(BLOCKSIZE)
            if len(block) > BLOCKSIZE * 20:
                logger.warning("Runaway header in EDF file")
                return
        start = block.find("{") + 1
        end = block.find("}")

        # Now it is essential to go to the start of the binary part
        if block[end: end + 3] == "}\r\n":
            offset = end + 3 - len(block)
        elif block[end: end + 2] == "}\n":
            offset = end + 2 - len(block)
        else:
            logger.error("Unable to locate start of the binary section")
            offset = None
        if offset is not None:
            infile.seek(offset, os.SEEK_CUR)
        return block[start:end]


    def _readheader(self, infile):
        """
        Read all headers in a file and populate self.header
        data is not yet populated
        @type infile: file object open in read mode
        """
        self.__frames = []
        bContinue = True
        while bContinue:
            block = self._readHeaderBlock(infile)
            if block is None:
                bContinue = False
                break
            frame = Frame(number=self.nframes)
            size = frame.parseheader(block)
            frame.file = infile
            frame.start = infile.tell()
            frame.size = size
            self.__frames += [frame]
            try:
                infile.seek(size, os.SEEK_CUR)
            except Exception, error:
                logger.warning("infile is %s" % infile)
                logger.warning("Position is %s" % infile.tell())
                logger.warning("size is %s" % size)
                logger.error("It seams this error occurs under windows when reading a (large-) file over network: %s ", error)
                raise Exception(error)

            if  frame.start + size > infile.size:
                logger.warning("Non complete datablock: got %s, expected %s" % (infile.size - frame.start, size))
                bContinue = False
                break

        for i, frame in enumerate(self.__frames):
            missing = []
            for item in MINIMUM_KEYS:
                if item not in frame.capsHeader:
                    missing.append(item)
            if len(missing) > 0:
                logger.info("EDF file %s frame %i misses mandatory keys: %s " % (self.filename, i, " ".join(missing)))
        self.currentframe = 0


    def read(self, fname, frame=None):
        """
        Read in header into self.header and
            the data   into self.data
        """
        self.resetvals()
        self.filename = fname

        infile = self._open(fname, "rb")
        self._readheader(infile)
        if frame is None:
            pass
        elif frame < self.nframes:
            self = self.getframe(frame)
        else:
            logger.error("Reading file %s You requested frame %s but only %s frames are available", fname, frame, self.nframes)
        self.resetvals()
        # ensure the PIL image is reset
        self.pilimage = None
        return self

    def swap_needed(self):
        """
        Decide if we need to byteswap
        """
        if ('Low'  in self.header[self.capsHeader['BYTEORDER']] and numpy.little_endian) or \
           ('High' in self.header[self.capsHeader['BYTEORDER']] and not numpy.little_endian):
            return False
        if ('High'  in self.header[self.capsHeader['BYTEORDER']] and numpy.little_endian) or \
           ('Low' in self.header[self.capsHeader['BYTEORDER']] and not numpy.little_endian):
            if self.bpp in [2, 4, 8]:
                return True
            else:
                return False

    def unpack(self):
        """
        Unpack a binary blob according to the specification given in the header and return the dataset

        @return: dataset as numpy.ndarray
        """
        return self.__frames[self.currentframe].getData()


    def getframe(self, num):
        """ returns the file numbered 'num' in the series as a fabioimage """
        newImage = None
        if self.nframes == 1:
            logger.debug("Single frame EDF; having fabioimage default behavour: %s" % num)
            newImage = fabioimage.getframe(self, num)
        elif num in xrange(self.nframes):
            logger.debug("Multi frame EDF; having edfimage specific behavour: %s/%s" % (num, self.nframes))
            newImage = edfimage(frames=self.__frames)
            newImage.currentframe = num
            newImage.filename = self.filename
        else:
            txt = "Cannot access frame: %s/%s" % (num, self.nframes)
            logger.error(txt)
            raise ValueError("edfimage.getframe:" + txt)
        return newImage


    def previous(self):
        """ returns the previous file in the series as a fabioimage """
        newImage = None
        if self.nframes == 1:
            newImage = fabioimage.previous(self)
        else:
            newFrameId = self.currentframe - 1
            newImage = self.getframe(newFrameId)
        return newImage


    def next(self):
        """ returns the next file in the series as a fabioimage """
        newImage = None
        if self.nframes == 1:
            newImage = fabioimage.next(self)
        else:
            newFrameId = self.currentframe + 1
            newImage = self.getframe(newFrameId)
        return newImage


    def write(self, fname, force_type=None, fit2dMode=False):
        """
        Try to write a file
        check we can write zipped also
        mimics that fabian was writing uint16 (we sometimes want floats)

        @param force_type: can be numpy.uint16 or simply "float"
        @return: None

        """

        outfile = self._open(fname, mode="wb")
        for i, frame in enumerate(self.__frames):
            frame.iFrame = i
            outfile.write(frame.getEdfBlock(force_type=force_type, fit2dMode=fit2dMode))
        outfile.close()


    def appendFrame(self, frame=None, data=None, header=None):
        """
        Method used add a frame to an EDF file
        @param frame: frame to append to edf image
        @type frame: instance of Frame
        @return: None
        """
        if isinstance(frame, Frame):
            self.__frames.append(frame)
        else:
            self.__frames.append(Frame(data, header))


    def deleteFrame(self, frameNb=None):
        """
        Method used to remove a frame from an EDF image. by default the last one is removed.
        @param frameNb: frame number to remove, by  default the last.
        @type frameNb: integer
        @return: None
        """
        if frameNb is None:
            self.__frames.pop()
        else:
            self.__frames.pop(frameNb)

    def fastReadData(self, filename=None):
        """
        This is a special method that will read and return the data from another file ...
        The aim is performances, ... but only supports uncompressed files. 
         
        @return: data from another file using positions from current edfimage
        """
        if (filename is None) or not os.path.isfile(filename):
            raise RuntimeError("edfimage.fastReadData is only valid with another file: %s does not exist" % (filename))
        data = None
        frame = self.__frames[self.currentframe]
        with open(filename, "rb")as f:
            f.seek(frame.start)
            raw = f.read(frame.size)
        try:
            data = numpy.fromstring(raw, dtype=self.bytecode)
            data.shape = self.data.shape
        except Exception, err :
            logger.error("unable to convert file content to numpy array: %s", err)
        return data

    def fastReadROI(self, filename, coords=None):
        """
        Method reading Region of Interest of another file  based on metadata available in current edfimage.
        The aim is performances, ... but only supports uncompressed files.
        
        @return: ROI-data from another file using positions from current edfimage
        @rtype: numpy 2darray
        """
        if (filename is None) or not os.path.isfile(filename):
            raise RuntimeError("edfimage.fastReadData is only valid with another file: %s does not exist" % (filename))
        data = None
        frame = self.__frames[self.currentframe]

        if len(coords) == 4:
            slice1 = self.make_slice(coords)
        elif len(coords) == 2 and isinstance(coords[0], slice) and \
                                  isinstance(coords[1], slice):
            slice1 = coords
        else:
            logger.warning('readROI: Unable to understand Region Of Interest: got %s', coords)
            return
        d1 = self.data.shape[-1]
        start0 = slice1[0].start
        start1 = slice1[1].start
        slice2 = (slice(0, slice1[0].stop - start0, slice1[0].step),
                   slice(0, slice1[1].stop - start1, slice1[1].step))
        start = frame.start + self.bpp * (d1 * start0 + start1)
        size = self.bpp * ((slice2[0].stop) * d1)
        with open(filename, "rb")as f:
            f.seek(start)
            raw = f.read(size)
        try:
            data = numpy.fromstring(raw, dtype=self.bytecode)
            data.shape = -1, d1
        except Exception, err :
            logger.error("unable to convert file content to numpy array: %s", err)
        return data[slice2]


################################################################################
# Properties definition for header, data, header_keys and capsHeader
################################################################################
    def getNbFrames(self):
        """
        Getter for number of frames
        """
        return len(self.__frames)
    def setNbFrames(self, val):
        """
        Setter for number of frames ... should do nothing. Here just to avoid bugs
        """
        if val != len(self.__frames):
            logger.warning("trying to set the number of frames ")
    nframes = property(getNbFrames, setNbFrames, "property: number of frames in EDF file")


    def getHeader(self):
        """
        Getter for the headers. used by the property header,
        """
        return self.__frames[self.currentframe].header
    def setHeader(self, _dictHeader):
        """
        Enforces the propagation of the header to the list of frames
        """
        try:
            self.__frames[self.currentframe].header = _dictHeader
        except AttributeError:
            self.__frames = [Frame(header=_dictHeader)]
        except IndexError:
            if self.currentframe < len(self.__frames):
                self.__frames.append(Frame(header=_dictHeader))
    def delHeader(self):
        """
        Deleter for edf header
        """
        self.__frames[self.currentframe].header = {}
    header = property(getHeader, setHeader, delHeader, "property: header of EDF file")

    def getHeaderKeys(self):
        """
        Getter for edf header_keys
        """
        return self.__frames[self.currentframe].header_keys
    def setHeaderKeys(self, _listtHeader):
        """
        Enforces the propagation of the header_keys to the list of frames
        @param _listtHeader: list of the (ordered) keys in the header
        @type _listtHeader: python list
        """
        try:
            self.__frames[self.currentframe].header_keys = _listtHeader
        except AttributeError:
            self.__frames = [Frame(header_keys=_listtHeader)]
        except IndexError:
            if self.currentframe < len(self.__frames):
                self.__frames.append(Frame(header_keys=_listtHeader))
    def delHeaderKeys(self):
        """
        Deleter for edf header_keys
        """
        self.__frames[self.currentframe].header_keys = []
    header_keys = property(getHeaderKeys, setHeaderKeys, delHeaderKeys, "property: header_keys of EDF file")

    def getData(self):
        """
        getter for edf Data
        @return: data for current frame
        @rtype: numpy.ndarray
        """
        npaData = None
        try:
            npaData = self.__frames[self.currentframe].data
        except AttributeError:
            self.__frames = [Frame()]
            npaData = self.__frames[self.currentframe].data
        except IndexError:
            if self.currentframe < len(self.__frames):
                self.__frames.append(Frame())
                npaData = self.__frames[self.currentframe].data
        return npaData

    def setData(self, _data):
        """
        Enforces the propagation of the data to the list of frames
        @param _data: numpy array representing data
        """
        try:
            self.__frames[self.currentframe].data = _data
        except AttributeError:
            self.__frames = [Frame(data=_data)]
        except IndexError:
            if self.currentframe < len(self.__frames):
                self.__frames.append(Frame(data=_data))
    def delData(self):
        """
        deleter for edf Data
        """
        self.__frames[self.currentframe].data = None
    data = property(getData, setData, delData, "property: data of EDF file")

    def getCapsHeader(self):
        """
        getter for edf headers keys in upper case
        @return: data for current frame
        @rtype: dict
        """
        return self.__frames[self.currentframe].capsHeader
    def setCapsHeader(self, _data):
        """
        Enforces the propagation of the header_keys to the list of frames
        @param _data: numpy array representing data
        """
        self.__frames[self.currentframe].capsHeader = _data
    def delCapsHeader(self):
        """
        deleter for edf capsHeader
        """
        self.__frames[self.currentframe].capsHeader = {}
    capsHeader = property(getCapsHeader, setCapsHeader, delCapsHeader, "property: capsHeader of EDF file, i.e. the keys of the header in UPPER case.")

    def getDim1(self):
        return self.__frames[self.currentframe].dim1
    def setDim1(self, _iVal):
        try:
            self.__frames[self.currentframe].dim1 = _iVal
        except AttributeError:
            self.__frames = [Frame()]
        except IndexError:
            if self.currentframe < len(self.__frames):
                self.__frames.append(Frame())
                self.__frames[self.currentframe].dim1 = _iVal
    dim1 = property(getDim1, setDim1)
    def getDim2(self):
        return self.__frames[self.currentframe].dim2
    def setDim2(self, _iVal):
        try:
            self.__frames[self.currentframe].dim2 = _iVal
        except AttributeError:
            self.__frames = [Frame()]
        except IndexError:
            if self.currentframe < len(self.__frames):
                self.__frames.append(Frame())
                self.__frames[self.currentframe].dim2 = _iVal
    dim2 = property(getDim2, setDim2)

    def getDims(self):
        return self.__frames[self.currentframe].dims
    dims = property(getDims)
    def getByteCode(self):
        return self.__frames[self.currentframe].bytecode
    def setByteCode(self, _iVal):
        try:
            self.__frames[self.currentframe].bytecode = _iVal
        except AttributeError:
            self.__frames = [Frame()]
        except IndexError:
            if self.currentframe < len(self.__frames):
                self.__frames.append(Frame())
                self.__frames[self.currentframe].bytecode = _iVal
    bytecode = property(getByteCode, setByteCode)
    def getBpp(self):
        return self.__frames[self.currentframe].bpp
    def setBpp(self, _iVal):
        try:
            self.__frames[self.currentframe].bpp = _iVal
        except AttributeError:
            self.__frames = [Frame()]
        except IndexError:
            if self.currentframe < len(self.__frames):
                self.__frames.append(Frame())
                self.__frames[self.currentframe].bpp = _iVal
    bpp = property(getBpp, setBpp)

