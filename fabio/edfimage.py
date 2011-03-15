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
from fabioimage import fabioimage
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
                "Double"        :  np.float64,
                "DoubleValue"   :  np.float64,
                "FloatIEEE64"   :  np.float64,
                "DoubleIEEE64"  :  np.float64
                }

NUMPY_EDF_DTYPE = {"int8"       :"SignedByte",
                   "int16"      :"SignedShort",
                   "int32"      :"SignedInteger",
                   "int64"      :"Signed64",
                   "uint8"      :"UnsignedByte",
                   "uint16"     :"UnsignedShort",
                   "uint32"     :"UnsignedInteger",
                   "uint64"     :"Unsigned64",
                   "float32"    :"FloatValue",
                   "float64"    :"DoubleValue"
             }

MINIMUM_KEYS = ['HEADERID',
                'IMAGE',
                'BYTEORDER',
                'DATATYPE',
                'DIM_1',
                'DIM_2',
                'SIZE'] # Size is thought to be essential for writing at least

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
                    logging.warning("Header key %s, in header_keys is not in header dictionary, poping !!!" % key)
                    self.header_keys.remove(key)

        self.capsHeader = {}
        for key in self.header_keys:
            try:
                self.capsHeader[key.upper()] = key
            except AttributeError:
                logging.warning("Header key %s is not a string" % key)

        self.rawData = None
        self.data = data
        self.dims = []
        self.dim1 = 0
        self.dim2 = 0
        self.size = None
        self.bpp = None
        self.bytecode = None
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
                key = key.strip()
                self.header[key] = val.strip()
                self.capsHeader[key.upper()] = key
                self.header_keys.append(key)

        # Compute image size
        if "SIZE" in self.capsHeader:
            try:
                self.size = int(self.header[self.capsHeader["SIZE"]])
            except ValueError:
                logging.warning("Unable to convert to integer : %s %s " % (self.capsHeader["SIZE"], self.header[self.capsHeader["SIZE"]]))
        if "DIM_1" in self.capsHeader:
            try:
                dim1 = int(self.header[self.capsHeader['DIM_1']])
            except ValueError:
                logging.error("Unable to convert to integer Dim_1: %s %s" % (self.capsHeader["DIM_1"], self.header[self.capsHeader["DIM_1"]]))
            else:
                calcsize *= dim1
                self.dims.append(dim1)
        else:
            logging.error("No Dim_1 in headers !!!")
        if "DIM_2" in self.capsHeader:
            try:
                dim2 = int(self.header[self.capsHeader['DIM_2']])
            except ValueError:
                logging.error("Unable to convert to integer Dim_3: %s %s" % (self.capsHeader["DIM_2"], self.header[self.capsHeader["DIM_2"]]))
            else:
                calcsize *= dim2
                self.dims.append(dim2)
        else:
            logging.error("No Dim_2 in headers !!!")
        iDim = 3
        while iDim is not None:
            strDim = "DIM_%i" % iDim
            if strDim in self.capsHeader:
                try:
                    dim3 = int(self.header[self.capsHeader[strDim]])
                except ValueError:
                    logging.error("Unable to convert to integer %s: %s %s"
                                  % (strDim, self.capsHeader[strDim], self.header[self.capsHeader[strDim]]))
                    dim3 = None
                    iDim = None
                else:
                    calcsize *= dim3
                    self.dims.append(dim3)
                    iDim += 1
            else:
                logging.debug("No Dim_3 -> it is a 2D image")
                iDim = None
        if self.bytecode is None:
            if "DATATYPE" in self.capsHeader:
                self.bytecode = DATA_TYPES[self.header[self.capsHeader['DATATYPE']]]
            else:
                self.bytecode = np.uint16
                logging.warning("Defaulting type to uint16")
        self.bpp = len(np.array(0, self.bytecode).tostring())
        calcsize *= self.bpp
        if (self.size is None):
            self.size = calcsize
        elif (self.size != calcsize):
            if ("COMPRESSION" in self.capsHeader) and (self.header[self.capsHeader['COMPRESSION']].upper().startswith("NO")):
                logging.info("Mismatch between the expected size %s and the calculated one %s" % (self.size, calcsize))
                self.size = calcsize

        for i, n in enumerate(self.dims):
            exec "self.dim%i=%i" % (i + 1, n)

        return self.size


    def swap_needed(self):
        """
        Decide if we need to byteswap
        """
        if ('Low'  in self.header[self.capsHeader['BYTEORDER']] and np.little_endian) or \
           ('High' in self.header[self.capsHeader['BYTEORDER']] and not np.little_endian):
            return False
        if ('High'  in self.header[self.capsHeader['BYTEORDER']] and np.little_endian) or \
           ('Low' in self.header[self.capsHeader['BYTEORDER']] and not np.little_endian):
            if self.bpp in [2, 4, 8]:
                return True
            else:
                return False


    def getData(self):
        """
        Unpack a binary blob according to the specification given in the header

        @return: dataset as numpy.ndarray
        """
        if self.data is not None:
            return self.data
        if self.rawData is None:
            return self.data

        if self.bytecode is None:
            if "DATATYPE" in self.capsHeader:
                self.bytecode = DATA_TYPES[self.header[self.capsHeader["DATATYPE"]]]
            else:
                self.bytecode = np.uint16
        dims = self.dims[:]
        dims.reverse()

        if ("COMPRESSION" in self.capsHeader):
            compression = self.header[self.capsHeader["COMPRESSION"]].upper()
            uncompressed_size = self.bpp
            for i in dims:
                uncompressed_size *= i
            if "OFFSET" in compression :
                try:
                    import byte_offset
                except ImportError:
                    logging.error("Unimplemented compression scheme:  %s" % compression)
                else:
                    myData = byte_offset.analyseCython(self.rawData, size=uncompressed_size)
                    rawData = myData.astype(self.bytecode).tostring()
                    self.size = uncompressed_size
            elif compression == "NONE":
                rawData = self.rawData
            elif "GZIP" in compression:
                fileobj = StringIO.StringIO(self.rawData)
                try:
                    rawData = gzip.GzipFile(fileobj=fileobj).read()
                except IOError:
                    logging.warning("Encounter the python-gzip bug with trailing garbage")
                    #This is as an ugly hack against a bug in Python gzip
                    import subprocess
                    sub = subprocess.Popen(["gzip", "-d", "-f"], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
                    rawData, err = sub.communicate(input=self.rawData)
                    logging.debug("Gzip subprocess ended with %s err= %s; I got %s bytes back" % (sub.wait(), err, len(rawData)))
                self.size = uncompressed_size
            elif "BZ" in compression :
                rawData = bz2.decompress(self.rawData)
                self.size = uncompressed_size
            elif "Z" in compression :
                rawData = zlib.decompress(self.rawData)
                self.size = uncompressed_size
            else:
                logging.warning("Unknown compression scheme %s" % compression)
                rawData = self.rawData

        else:
            rawData = self.rawData

        expected = self.size
        obtained = len(rawData)
        if expected > obtained:
            logging.error("Data stream is incomplete: %s < expected %s bytes" % (obtained, expected))
            rawData += "\x00" * (expected - obtained)
        elif expected < len(rawData):
            logging.info("Data stream contains trailing junk : %s > expected %s bytes" % (obtained, expected))
            rawData = rawData[:expected]
#        logging.debug("dims = %s, bpp = %s, expected= %s obtained = %s" % (dims, self.bpp, expected, obtained))
        if self.swap_needed():
            data = np.fromstring(rawData, self.bytecode).byteswap().reshape(tuple(dims))
        else:
            data = np.fromstring(rawData, self.bytecode).reshape(tuple(dims))
        self.data = data
        self.rawData = None #no need to keep garbage in memory
        self.bytecode = data.dtype.type
        return data


    def getEdfBlock(self, force_type=None):
        """
        @param force_type: type of the dataset to be enforced like "float64" or "uint16"
        @type force_type: string or numpy.dtype
        @return: ascii header block 
        @rtype: python string with the concatenation of the ascii header and the binary data block
        """
        if force_type is not None:
            data = self.getData().astype(force_type)
        else:
            data = self.getData()

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
        header["HeaderID"] = "EH:%06d:000000:000000" % self.iFrame
        header_keys.insert(0, "Image")
        header["Image"] = str(self.iFrame)

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
        if not "EDF_DataBlockID" in header:
            header["EDF_DataBlockID"] = "%i.Image.Psd" % self.iFrame
        preciseSize = 4 #2 before {\n 2 after }\n
        for key in header_keys:
            line = str("%s = %s ;\n" % (key, header[key]))
            preciseSize += len(line)
            listHeader.append(line)
#            print type(line), line
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
        return "".join(listHeader) + data.tostring()



class edfimage(fabioimage):
    """ Read and try to write the ESRF edf data format """

    def __init__(self, data=None , header=None, header_keys=None):
        self.currentframe = 0
        fabioimage.__init__(self, data, header)
        frame = Frame(data=data, header=header,
                      header_keys=header_keys ,
                      number=self.currentframe)
        self.frames = [frame]


    @staticmethod
    def _readHeaderBlock(infile):
        """
        Read in a header in some EDF format from an already open file
        
        @param infile: file object open in read mode
        @return: string (or None if no header was found. 
        """

        block = infile.read(BLOCKSIZE)
        if len(block) < BLOCKSIZE:
            logging.debug("Under-short header: only %i bytes in %s" % (len(block), infile.name))
            return
        if (block.find("{") < 0) :
            # This does not look like an edf file
            logging.warning("no opening {. Corrupt header of EDF file %s" % infile.name)
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


    def _readheader(self, infile):
        """
        Read all headers in a file and populate self.header
        data is not yet populated
        @type infile: file object open in read mode
        """
        self.nframes = 0
        self.frames = []

        bContinue = True
        while bContinue:
            block = self._readHeaderBlock(infile)
            if block is None:
                bContinue = False
                break
            frame = Frame(number=self.nframes)
            self.frames.append(frame)
            size = frame.parseheader(block)
            frame.rawData = infile.read(size)
            if len(frame.rawData) != size:
                logging.warning("Non complete datablock: got %s, expected %s" % (len(frame.rawData), size))
                bContinue = False
                break
            self.nframes += 1

        for i, frame in enumerate(self.frames):
            missing = []
            for item in MINIMUM_KEYS:
                if item not in frame.capsHeader:
                    missing.append(item)
            if len(missing) > 0:
                logging.info("EDF file %s frame %i misses mandatory keys: %s " % (self.filename, i, " ".join(missing)))

        self.currentframe = 0


    def read(self, fname):
        """
        Read in header into self.header and
            the data   into self.data
        """
        self.resetvals()
        self.filename = fname

        infile = self._open(fname, "rb")
        self._readheader(infile)
        if self.data is None:
            self.data = self.unpack()
#            self.bytecode = self.data.dtype.type
        self.resetvals()
        # ensure the PIL image is reset
        self.pilimage = None
        return self

    def swap_needed(self):
        """
        Decide if we need to byteswap
        """
        if ('Low'  in self.header[self.capsHeader['BYTEORDER']] and np.little_endian) or \
           ('High' in self.header[self.capsHeader['BYTEORDER']] and not np.little_endian):
            return False
        if ('High'  in self.header[self.capsHeader['BYTEORDER']] and np.little_endian) or \
           ('Low' in self.header[self.capsHeader['BYTEORDER']] and not np.little_endian):
            if self.bpp in [2, 4, 8]:
                return True
            else:
                return False


    def unpack(self):
        """
        Unpack a binary blob according to the specification given in the header and return the dataset

        @return: dataset as numpy.ndarray
        """
        return self.frames[self.currentframe].getData()


    def getframe(self, num):
        """ returns the file numbered 'num' in the series as a fabioimage """
        if num in xrange(self.nframes):
            frame = self.frames[num]
            newImage = edfimage(data=frame.getData(), header=frame.header, header_keys=frame.header_keys)
            newImage.frames = self.frames
            newImage.nframes = self.nframes
            newImage.currentframe = num
            newImage.filename = self.filename
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
        outfile = self._open(fname, mode="wb")
        for i, frame in enumerate(self.frames):
            frame.iFrame = i
            outfile.write(frame.getEdfBlock())
        outfile.close()

################################################################################
# Properties definition for header, data, header_keys and capsHeader 
################################################################################

    def getHeader(self):
        """
        Getter for the headers. used by the property header,
        """
        return self.frames[self.currentframe].header
    def setHeader(self, _dictHeader):
        """
        Enforces the propagation of the header to the list of frames
        """
        try:
            self.frames[self.currentframe].header = _dictHeader
        except AttributeError:
            self.frames = [Frame(header=_dictHeader)]
        except IndexError:
            if self.currentframe < len(self.frames):
                self.frames.append(Frame(header=_dictHeader))
    def delHeader(self):
        """
        Deleter for edf header
        """
        self.frames[self.currentframe].header = {}
    header = property(getHeader, setHeader, delHeader, "property: header of EDF file")

    def getHeaderKeys(self):
        """
        Getter for edf header_keys
        """
        return self.frames[self.currentframe].header_keys
    def setHeaderKeys(self, _listtHeader):
        """
        Enforces the propagation of the header_keys to the list of frames
        @param _listtHeader: list of the (ordered) keys in the header
        @type _listtHeader: python list
        """
        try:
            self.frames[self.currentframe].header_keys = _listtHeader
        except AttributeError:
            self.frames = [Frame(header_keys=_listtHeader)]
        except IndexError:
            if self.currentframe < len(self.frames):
                self.frames.append(Frame(header_keys=_listtHeader))
    def delHeaderKeys(self):
        """
        Deleter for edf header_keys
        """
        self.frames[self.currentframe].header_keys = []
    header_keys = property(getHeaderKeys, setHeaderKeys, delHeaderKeys, "property: header_keys of EDF file")

    def getData(self):
        """
        getter for edf Data
        @return: data for current frame  
        @rtype: numpy.ndarray
        """
        data = None
        try:
            data = self.frames[self.currentframe].data
        except AttributeError:
            self.frames = [Frame()]
            data = self.frames[self.currentframe].data
        except IndexError:
            if self.currentframe < len(self.frames):
                self.frames.append(Frame())
                data = self.frames[self.currentframe].data
        return data

    def setData(self, _data):
        """
        Enforces the propagation of the header_keys to the list of frames
        @param _data: numpy array representing data 
        """
        try:
            self.frames[self.currentframe].data = _data
        except AttributeError:
            self.frames = [Frame(data=_data)]
        except IndexError:
            if self.currentframe < len(self.frames):
                self.frames.append(Frame(data=_data))
    def delData(self):
        """
        deleter for edf Data
        """
        self.frames[self.currentframe].data = None
    data = property(getData, setData, delData, "property: data of EDF file")

    def getCapsHeader(self):
        """
        getter for edf headers keys in upper case 
        @return: data for current frame  
        @rtype: dict
        """
        return self.frames[self.currentframe].capsHeader
    def setCapsHeader(self, _data):
        """
        Enforces the propagation of the header_keys to the list of frames
        @param _data: numpy array representing data 
        """
        self.frames[self.currentframe].capsHeader = _data
    def delCapsHeader(self):
        """
        deleter for edf capsHeader
        """
        self.frames[self.currentframe].capsHeader = {}
    capsHeader = property(getCapsHeader, setCapsHeader, delCapsHeader, "property: capsHeader of EDF file, i.e. the keys of the header in UPPER case.")

    def getDim1(self):
        return self.frames[self.currentframe].dim1
    def setDim1(self, _iVal):
        try:
            self.frames[self.currentframe].dim1 = _iVal
        except AttributeError:
            self.frames = [Frame()]
        except IndexError:
            if self.currentframe < len(self.frames):
                self.frames.append(Frame())
                self.frames[self.currentframe].dim1 = _iVal
    dim1 = property(getDim1, setDim1)
    def getDim2(self):
        return self.frames[self.currentframe].dim2
    def setDim2(self, _iVal):
        try:
            self.frames[self.currentframe].dim2 = _iVal
        except AttributeError:
            self.frames = [Frame()]
        except IndexError:
            if self.currentframe < len(self.frames):
                self.frames.append(Frame())
                self.frames[self.currentframe].dim2 = _iVal
    dim2 = property(getDim2, setDim2)

    def getDims(self):
        return self.frames[self.currentframe].dims
    dims = property(getDims)
    def getByteCode(self):
        return self.frames[self.currentframe].bytecode
    def setByteCode(self, _iVal):
        try:
            self.frames[self.currentframe].bytecode = _iVal
        except AttributeError:
            self.frames = [Frame()]
        except IndexError:
            if self.currentframe < len(self.frames):
                self.frames.append(Frame())
                self.frames[self.currentframe].bytecode = _iVal

    bytecode = property(getByteCode, setByteCode)
    def getBpp(self):
        return self.frames[self.currentframe].bpp
    def setBpp(self, _iVal):
        try:
            self.frames[self.currentframe].bpp = _iVal
        except AttributeError:
            self.frames = [Frame()]
        except IndexError:
            if self.currentframe < len(self.frames):
                self.frames.append(Frame())
                self.frames[self.currentframe].bpp = _iVal
    bpp = property(getBpp, setBpp)

