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
#  Permission is hereby granted, free of charge, to any person
#  obtaining a copy of this software and associated documentation files
#  (the "Software"), to deal in the Software without restriction,
#  including without limitation the rights to use, copy, modify, merge,
#  publish, distribute, sublicense, and/or sell copies of the Software,
#  and to permit persons to whom the Software is furnished to do so,
#  subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be
#  included in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
#  OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#  NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#  HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
#  WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION W

"""

License: MIT

Authors:
........
* Henning O. Sorensen & Erik Knudsen:
  Center for Fundamental Research: Metal Structures in Four Dimensions;
  Risoe National Laboratory;
  Frederiksborgvej 399;
  DK-4000 Roskilde;
  email:erik.knudsen@risoe.dk
* Jon Wright & Jérôme Kieffer:
  European Synchrotron Radiation Facility;
  Grenoble (France)


"""
# get ready for python3
from __future__ import with_statement, print_function, absolute_import, division
import os
import re
import string
import logging
logger = logging.getLogger(__name__)
import numpy
from .fabioimage import FabioImage, OrderedDict
from .fabioutils import isAscii, toAscii, nice_int
from .compression import decBzip2, decGzip, decZlib
from . import compression as compression_module
from . import fabioutils


BLOCKSIZE = 512
MAX_BLOCKS = 40
DATA_TYPES = {"SignedByte": numpy.int8,
              "Signed8": numpy.int8,
              "UnsignedByte": numpy.uint8,
              "Unsigned8": numpy.uint8,
              "SignedShort": numpy.int16,
              "Signed16": numpy.int16,
              "UnsignedShort": numpy.uint16,
              "Unsigned16": numpy.uint16,
              "UnsignedShortInteger": numpy.uint16,
              "SignedInteger": numpy.int32,
              "Signed32": numpy.int32,
              "UnsignedInteger": numpy.uint32,
              "Unsigned32": numpy.uint32,
              "SignedLong": numpy.int32,
              "UnsignedLong": numpy.uint32,
              "Signed64": numpy.int64,
              "Unsigned64": numpy.uint64,
              "FloatValue": numpy.float32,
              "FLOATVALUE": numpy.float32,
              "FLOAT": numpy.float32,  # fit2d
              "Float": numpy.float32,  # fit2d
              "FloatIEEE32": numpy.float32,
              "Float32": numpy.float32,
              "Double": numpy.float64,
              "DoubleValue": numpy.float64,
              "FloatIEEE64": numpy.float64,
              "DoubleIEEE64": numpy.float64}
try:
    DATA_TYPES["FloatIEEE128"] = DATA_TYPES["DoubleIEEE128"] = DATA_TYPES["QuadrupleValue"] = numpy.float128

except AttributeError:
    # not in your numpy
    logger.debug("No support for float128 in your code")

NUMPY_EDF_DTYPE = {"int8": "SignedByte",
                   "int16": "SignedShort",
                   "int32": "SignedInteger",
                   "int64": "Signed64",
                   "uint8": "UnsignedByte",
                   "uint16": "UnsignedShort",
                   "uint32": "UnsignedInteger",
                   "uint64": "Unsigned64",
                   "float32": "FloatValue",
                   "float64": "DoubleValue",
                   "float128": "QuadrupleValue",
                   }

MINIMUM_KEYS = set(['HEADERID',
                    'IMAGE',
                    'BYTEORDER',
                    'DATATYPE',
                    'DIM_1',
                    'DIM_2',
                    'SIZE'])  # Size is thought to be essential for writing at least

DEFAULT_VALUES = {}
# I do not define default values as they will be calculated at write time
# JK20110415


class MalformedHeaderError(IOError):
    """Raised when a header is malformed"""
    pass


class Frame(object):
    """
    A class representing a single frame in an EDF file
    """
    def __init__(self, data=None, header=None, number=None):

        self.header = EdfImage.check_header(header)

        self._data_compression = None
        self._data_swap_needed = None
        self._data = data
        self.dims = []
        self.dim1 = 0
        self.dim2 = 0
        self.start = None  # Position of start of raw data in file
        self.size = None  # size of raw data in file
        self.file = None  # opened file object with locking capabilities !!!
        self.bpp = None
        self.incomplete_data = False
        self._bytecode = None

        if (number is not None):
            self.iFrame = int(number)
        else:
            self.iFrame = 0

    def _compute_capsheader(self):
        """
        Returns the mapping from capitalized keys of the header to the original
        keys.

        :rtype: dict
        """
        capsHeader = {}
        for key in self.header:
            upperkey = key.upper()
            if upperkey not in capsHeader:
                capsHeader[upperkey] = key
        return capsHeader

    def _extract_header_metadata(self, capsHeader=None):
        """Extract from the header metadata expected to read the data.

        Store them in this frame.

        :param dict capsHeader: Precached mapping from capitalized keys of the
            header to the original keys.
        """
        self.size = None
        calcsize = 1
        self.dims = []

        if capsHeader is None:
            capsHeader = self._compute_capsheader()

        # Compute image size
        if "SIZE" in capsHeader:
            try:
                self.size = nice_int(self.header[capsHeader["SIZE"]])
            except ValueError:
                logger.warning("Unable to convert to integer : %s %s " % (capsHeader["SIZE"], self.header[capsHeader["SIZE"]]))
        if "DIM_1" in capsHeader:
            try:
                dim1 = nice_int(self.header[capsHeader['DIM_1']])
            except ValueError:
                logger.error("Unable to convert to integer Dim_1: %s %s" % (capsHeader["DIM_1"], self.header[capsHeader["DIM_1"]]))
            else:
                calcsize *= dim1
                self.dims.append(dim1)
        else:
            logger.error("No Dim_1 in headers !!!")
        if "DIM_2" in capsHeader:
            try:
                dim2 = nice_int(self.header[capsHeader['DIM_2']])
            except ValueError:
                logger.error("Unable to convert to integer Dim_2: %s %s" % (capsHeader["DIM_2"], self.header[capsHeader["DIM_2"]]))
            else:
                calcsize *= dim2
                self.dims.append(dim2)
        else:
            logger.error("No Dim_2 in headers !!!")
        iDim = 3
        # JON: this appears to be for nD images, but we don't treat those
        while iDim is not None:
            strDim = "DIM_%i" % iDim
            if strDim in capsHeader:
                try:
                    dim3 = nice_int(self.header[capsHeader[strDim]])
                except ValueError:
                    logger.error("Unable to convert to integer %s: %s %s",
                                 strDim, capsHeader[strDim], self.header[capsHeader[strDim]])
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
            if "DATATYPE" in capsHeader:
                self._bytecode = DATA_TYPES[self.header[capsHeader['DATATYPE']]]
            else:
                self._bytecode = numpy.uint16
                logger.warning("Defaulting type to uint16")

        if "COMPRESSION" in capsHeader:
            self._data_compression = self.header[capsHeader["COMPRESSION"]].upper()
            if self._data_compression == "NONE":
                self._data_compression = None
            elif self._data_compression.startswith("NO"):
                self._data_compression = None
        else:
            self._data_compression = None

        self.bpp = len(numpy.array(0, self._bytecode).tostring())
        calcsize *= self.bpp
        if (self.size is None):
            self.size = calcsize
        elif (self.size != calcsize):
            if self._data_compression is None:
                logger.warning("Mismatch between the expected size %s and the calculated one %s", self.size, calcsize)
                self.size = calcsize

        for i, n in enumerate(self.dims):
            setattr(self, "dim%i" % (i + 1), n)

        byte_order = self.header[capsHeader['BYTEORDER']]
        if ('Low' in byte_order and numpy.little_endian) or \
           ('High' in byte_order and not numpy.little_endian):
            self._data_swap_needed = False
        if ('High' in byte_order and numpy.little_endian) or \
           ('Low' in byte_order and not numpy.little_endian):
            if self.bpp in [2, 4, 8]:
                self._data_swap_needed = True
            else:
                self._data_swap_needed = False

    def parseheader(self, block):
        """
        Parse the header in some EDF format from an already open file

        :param str block: string representing the header block.
        :return: size of the binary blob
        """
        # reset values
        self.header = OrderedDict()
        capsHeader = {}

        # Why would someone put null bytes in a header?
        whitespace = string.whitespace + "\x00"

        for line in block.split(';'):
            if '=' in line:
                key, val = line.split('=', 1)
                key = key.strip(whitespace)
                self.header[key] = val.strip(whitespace)
                capsHeader[key.upper()] = key

        self._extract_header_metadata(capsHeader)

        return self.size

    def _check_header_mandatory_keys(self, filename=''):
        """Check that frame header contains all mandatory keys

        :param str filename: Name of the EDF file
        :rtype: bool
        """
        capsKeys = set([k.upper() for k in self.header.keys()])
        missing = list(MINIMUM_KEYS - capsKeys)
        if len(missing) > 0:
            logger.info("EDF file %s frame %i misses mandatory keys: %s ",
                        filename,
                        self.iFrame,
                        " ".join(missing))
        return len(missing) == 0

    def swap_needed(self):
        """
        Decide if we need to byteswap
        """
        return self._data_swap_needed

    def getData(self):
        """
        Unpack a binary blob according to the specification given in the header

        :return: dataset as numpy.ndarray
        """
        data = None
        if self._data is not None:
            data = self._data
        elif self.file is None:
            data = self._data
        else:
            if self._bytecode is None:
                assert(False)
            dims = self.dims[:]
            dims.reverse()
            with self.file.lock:
                if self.file.closed:
                    logger.error("file: %s from %s is closed. Cannot read data." % (self.file, self.file.filename))
                    return
                else:
                    self.file.seek(self.start)
                    try:
                        fileData = self.file.read(self.size)
                    except Exception as e:
                        if isinstance(self.file, fabioutils.GzipFile):
                            if compression_module.is_incomplete_gz_block_exception(e):
                                return numpy.zeros(dims)
                        raise e

            if self._data_compression is not None:
                compression = self._data_compression
                uncompressed_size = self.bpp
                for i in dims:
                    uncompressed_size *= i
                if "OFFSET" in compression:
                    try:
                        import byte_offset  # IGNORE:F0401
                    except ImportError as error:
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
                elif "BZ" in compression:
                    rawData = decBzip2(fileData)
                    self.size = uncompressed_size
                elif "Z" in compression:
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
                rawData += "\x00".encode("ascii") * (expected - obtained)
            elif expected < len(rawData):
                logger.info("Data stream contains trailing junk : %s > expected %s bytes" % (obtained, expected))
                rawData = rawData[:expected]
            data = numpy.frombuffer(rawData, self._bytecode).copy().reshape(tuple(dims))
            if self.swap_needed():
                data.byteswap(True)
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
        :param force_type: type of the dataset to be enforced like "float64" or "uint16"
        :type force_type: string or numpy.dtype
        :param boolean fit2dMode: enforce compatibility with fit2d and starts counting number of images at 1
        :return: ascii header block + binary data block
        :rtype: python bytes with the concatenation of the ascii header and the binary data block
        """
        if force_type is not None:
            data = self.data.astype(force_type)
        else:
            data = self.data
        fit2dMode = bool(fit2dMode)

        # Compute map from normalized upper key to original key in the header
        capsHeader = {}
        for key in self.header:
            upperkey = key.upper()
            if upperkey not in capsHeader:
                capsHeader[upperkey] = key

        header = self.header.copy()
        header_keys = list(self.header.keys())

        listHeader = ["{\n"]
        # First of all clean up the headers:
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
            # but do not remove the value from dict, instead reset the key ...
            if capsHeader["EDF_DATABLOCKID"] != "EDF_DataBlockID":
                header["EDF_DataBlockID"] = header.pop(capsHeader["EDF_DATABLOCKID"])
                capsHeader["EDF_DATABLOCKID"] = "EDF_DataBlockID"

        # Then update static headers freshly deleted
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
        header["EDF_HeaderSize"] = "%5s" % (approxHeaderSize)
        header_keys.insert(0, "EDF_BinarySize")
        header["EDF_BinarySize"] = data.nbytes
        header_keys.insert(0, "EDF_DataBlockID")
        if "EDF_DataBlockID" not in header:
            header["EDF_DataBlockID"] = "%i.Image.Psd" % (self.iFrame + fit2dMode)
        preciseSize = 4  # 2 before {\n 2 after }\n
        for key in header_keys:
            # Escape keys or values that are no ascii
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
            for idx, line in enumerate(listHeader[:]):
                if line.startswith("EDF_HeaderSize"):
                    headerSize = BLOCKSIZE * (preciseSize // BLOCKSIZE + 1)
                    newline = "EDF_HeaderSize = %5s ;\n" % headerSize
                    delta = len(newline) - len(line)
                    if (preciseSize // BLOCKSIZE) != ((preciseSize + delta) // BLOCKSIZE):
                        headerSize = BLOCKSIZE * ((preciseSize + delta) // BLOCKSIZE + 1)
                        newline = "EDF_HeaderSize = %5s ;\n" % headerSize
                    preciseSize = preciseSize + delta
                    listHeader[idx] = newline
                    break
        else:
            headerSize = approxHeaderSize
        listHeader.append(" " * (headerSize - preciseSize) + "}\n")
        return ("".join(listHeader)).encode("ASCII") + data.tostring()


class EdfImage(FabioImage):
    """ Read and try to write the ESRF edf data format """

    DESCRIPTION = "European Synchrotron Radiation Facility data format"

    DEFAULT_EXTENSIONS = ["edf", "cor"]

    RESERVED_HEADER_KEYS = ['HEADERID', 'IMAGE', 'BYTEORDER', 'DATATYPE',
                            'DIM_1', 'DIM_2', 'DIM_3', 'SIZE']

    def __init__(self, data=None, header=None, frames=None):
        self.currentframe = 0
        self.filesize = None
        self._incomplete_file = False

        if data is None:
            # In case of creation of an empty instance
            stored_data = None
        else:
            try:
                dim = len(data.shape)
            except Exception as error:  # IGNORE:W0703
                logger.debug("Data don't look like a numpy array (%s), resetting all!!" % error)
                dim = 0

            if dim == 0:
                raise Exception("Data with empty shape is unsupported")
            elif dim == 1:
                logger.warning("Data in 1d dimension will be stored as a 2d dimension array")
                # make sure we do not change the shape of the input data
                stored_data = numpy.array(data, copy=False)
                stored_data.shape = (1, len(data))
            elif dim == 2:
                stored_data = data
            elif dim >= 3:
                raise Exception("Data dimension too big. Only 1d or 2d arrays are supported.")

        FabioImage.__init__(self, stored_data, header)

        if frames is None:
            frame = Frame(data=self.data, header=self.header,
                          number=self.currentframe)
            self._frames = [frame]
        else:
            self._frames = frames

    @staticmethod
    def check_header(header=None):
        """
        Empty for FabioImage but may be populated by others classes
        """
        if not isinstance(header, dict):
            return OrderedDict()
        new = OrderedDict()
        for key, value in header.items():
            new[toAscii(key, ";{}")] = toAscii(value, ";{}")
        return new

    @staticmethod
    def _readHeaderBlock(infile, frame_id):
        """
        Read in a header in some EDF format from an already open file

        :param fileid infile: file object open in read mode
        :param int frame_id: Informative frame ID
        :return: string (or None if no header was found.
        :raises MalformedHeaderError: If the header can't be read
        """
        MAX_HEADER_SIZE = BLOCKSIZE * MAX_BLOCKS
        try:
            block = infile.read(BLOCKSIZE)
        except Exception as e:
            if isinstance(infile, fabioutils.GzipFile):
                if compression_module.is_incomplete_gz_block_exception(e):
                    raise MalformedHeaderError("Incomplete GZ block for header frame %i", frame_id)
            raise e

        if len(block) == 0:
            # end of file
            return None

        begin_block = block.find(b"{")
        if begin_block < 0:
            if len(block) < BLOCKSIZE and len(block.strip()) == 0:
                # Empty block looks to be a valid end of file
                return None
            logger.debug("Malformed header: %s", block)
            raise MalformedHeaderError("Header frame %i do not contains '{'" % frame_id)

        start = block[0:begin_block]
        if start.strip() != b"":
            logger.debug("Malformed header: %s", start)
            raise MalformedHeaderError("Header frame %i contains non-whitespace before '{'" % frame_id)

        if len(block) < BLOCKSIZE:
            logger.warning("Under-short header frame %i: only %i bytes", frame_id, len(block))

        # skip the open block character
        begin_block = begin_block + 1

        start = block.find(b"EDF_HeaderSize", begin_block)
        if start >= 0:
            equal = block.index(b"=", start + len(b"EDF_HeaderSize"))
            end = block.index(b";", equal + 1)
            try:
                chunk = block[equal + 1:end].strip()
                new_max_header_size = int(chunk)
            except Exception:
                logger.warning("Unable to read header size, got: %s", chunk)
            else:
                if new_max_header_size > MAX_HEADER_SIZE:
                    logger.info("Redefining MAX_HEADER_SIZE to %s", new_max_header_size)
                    MAX_HEADER_SIZE = new_max_header_size

        block_size = len(block)
        blocks = [block]

        end_pattern = re.compile(b"}[\r\n]")

        while True:
            end = end_pattern.search(block)
            if end is not None:
                end_block = block_size - len(block) + end.start()
                break
            block = infile.read(BLOCKSIZE)
            block_size += len(block)
            blocks.append(block)
            if len(block) == 0 or block_size > MAX_HEADER_SIZE:
                block = b"".join(blocks)
                logger.debug("Runaway header in EDF file MAX_HEADER_SIZE: %s\n%s", MAX_HEADER_SIZE, block)
                raise MalformedHeaderError("Runaway header frame %i (max size: %i)" % (frame_id, MAX_HEADER_SIZE))

        block = b"".join(blocks)

        # Now it is essential to go to the start of the binary part
        if block[end_block: end_block + 3] == b"}\r\n":
            offset = end_block + 3 - len(block)
        elif block[end_block: end_block + 2] == b"}\n":
            offset = end_block + 2 - len(block)
        else:
            logger.warning("Malformed end of header block")
            offset = end_block + 2 - len(block)

        infile.seek(offset, os.SEEK_CUR)
        return block[begin_block:end_block].decode("ASCII")

    @property
    def incomplete_file(self):
        """Returns true if the file is not complete.

        :rtype: bool
        """
        return self._incomplete_file

    def _readheader(self, infile):
        """
        Read all headers in a file and populate self.header
        data is not yet populated
        :type infile: file object open in read mode
        """
        self._frames = []

        while True:
            try:
                block = self._readHeaderBlock(infile, len(self._frames))
            except MalformedHeaderError:
                logger.debug("Backtrace", exc_info=True)
                if len(self._frames) == 0:
                    raise IOError("Invalid first header")
                self._incomplete_file = True
                break

            if block is None:
                # end of file
                if len(self._frames) == 0:
                    raise IOError("Empty file")
                break

            frame = Frame(number=self.nframes)
            size = frame.parseheader(block)
            frame.file = infile
            frame.start = infile.tell()
            frame.size = size
            self._frames += [frame]

            try:
                # skip the data block
                infile.seek(size - 1, os.SEEK_CUR)
                data = infile.read(1)
                if len(data) == 0:
                    self._incomplete_file = True
                    frame.incomplete_data = True
                    # Out of the file
                    break
            except Exception as error:
                if isinstance(infile, fabioutils.GzipFile):
                    if compression_module.is_incomplete_gz_block_exception(error):
                        self._incomplete_file = True
                        frame.incomplete_data = True
                        break
                logger.warning("infile is %s" % infile)
                logger.warning("Position is %s" % infile.tell())
                logger.warning("size is %s" % size)
                logger.error("It seams this error occurs under windows when reading a (large-) file over network: %s ", error)
                raise Exception(error)

        for frame in self._frames:
            frame._check_header_mandatory_keys(filename=self.filename)
        self.currentframe = 0

    def read(self, fname, frame=None):
        """
        Read in header into self.header and
            the data   into self.data
        """
        self.resetvals()
        self.filename = fname

        infile = self._open(fname, "rb")
        try:
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
        except Exception as e:
            infile.close()
            raise e
        return self

    def swap_needed(self):
        """
        Decide if we need to byteswap

        :return: True if needed, False else and None if not understood
        """
        return self._frames[self.currentframe].swap_needed()

    def unpack(self):
        """
        Unpack a binary blob according to the specification given in the header and return the dataset

        :return: dataset as numpy.ndarray
        """
        return self._frames[self.currentframe].getData()

    def getframe(self, num):
        """ returns the file numbered 'num' in the series as a FabioImage """
        newImage = None
        if self.nframes == 1:
            logger.debug("Single frame EDF; having FabioImage default behavior: %s" % num)
            newImage = FabioImage.getframe(self, num)
            newImage._file = self._file
        elif num < self.nframes:
            logger.debug("Multi frame EDF; having EdfImage specific behavior: %s/%s" % (num, self.nframes))
            newImage = self.__class__(frames=self._frames)
            newImage.currentframe = num
            newImage.filename = self.filename
            newImage._file = self._file
        else:
            raise IOError("EdfImage.getframe: Cannot access frame: %s/%s" %
                          (num, self.nframes))
        return newImage

    def previous(self):
        """ returns the previous file in the series as a FabioImage """
        newImage = None
        if self.nframes == 1:
            newImage = FabioImage.previous(self)
        else:
            newFrameId = self.currentframe - 1
            newImage = self.getframe(newFrameId)
        return newImage

    def next(self):
        """Returns the next file in the series as a fabioimage

        :raise IOError: When there is no next file or image in the series.
        """
        newImage = None
        if self.nframes == 1:
            newImage = FabioImage.next(self)
        else:
            newFrameId = self.currentframe + 1
            newImage = self.getframe(newFrameId)
        return newImage

    def write(self, fname, force_type=None, fit2dMode=False):
        """
        Try to write a file
        check we can write zipped also
        mimics that fabian was writing uint16 (we sometimes want floats)

        :param force_type: can be numpy.uint16 or simply "float"
        """
        # correct for bug #27: read all data before opening the file in write mode
        if fname == self.filename:
            [(frame.header, frame.data) for frame in self._frames]
            # this is thrown away
        with self._open(fname, mode="wb") as outfile:
            for i, frame in enumerate(self._frames):
                frame.iFrame = i
                outfile.write(frame.getEdfBlock(force_type=force_type, fit2dMode=fit2dMode))

    def appendFrame(self, frame=None, data=None, header=None):
        """
        Method used add a frame to an EDF file
        :param frame: frame to append to edf image
        :type frame: instance of Frame
        """
        if isinstance(frame, Frame):
            self._frames.append(frame)
        elif ("header" in dir(frame)) and ("data" in dir(frame)):
            self._frames.append(Frame(frame.data, frame.header))
        else:
            self._frames.append(Frame(data, header))

    def deleteFrame(self, frameNb=None):
        """
        Method used to remove a frame from an EDF image. by default the last one is removed.
        :param int frameNb: frame number to remove, by  default the last.
        """
        if frameNb is None:
            self._frames.pop()
        else:
            self._frames.pop(frameNb)

    def fastReadData(self, filename=None):
        """
        This is a special method that will read and return the data from another file ...
        The aim is performances, ... but only supports uncompressed files.

        :return: data from another file using positions from current EdfImage
        """
        if (filename is None) or not os.path.isfile(filename):
            raise RuntimeError("EdfImage.fastReadData is only valid with another file: %s does not exist" % (filename))
        data = None
        frame = self._frames[self.currentframe]
        with open(filename, "rb")as f:
            f.seek(frame.start)
            raw = f.read(frame.size)
        try:
            data = numpy.frombuffer(raw, dtype=self.bytecode).copy()
            data.shape = self.data.shape
        except Exception as error:
            logger.error("unable to convert file content to numpy array: %s", error)
        if frame.swap_needed():
            data.byteswap(True)
        return data

    def fastReadROI(self, filename, coords=None):
        """
        Method reading Region of Interest of another file  based on metadata available in current EdfImage.
        The aim is performances, ... but only supports uncompressed files.

        :return: ROI-data from another file using positions from current EdfImage
        :rtype: numpy 2darray
        """
        if (filename is None) or not os.path.isfile(filename):
            raise RuntimeError("EdfImage.fastReadData is only valid with another file: %s does not exist" % (filename))
        data = None
        frame = self._frames[self.currentframe]

        if len(coords) == 4:
            slice1 = self.make_slice(coords)
        elif (len(coords) == 2 and isinstance(coords[0], slice) and
              isinstance(coords[1], slice)):
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
            data = numpy.frombuffer(raw, dtype=self.bytecode).copy()
            data.shape = -1, d1
        except Exception as error:
            logger.error("unable to convert file content to numpy array: %s", error)
        if frame.swap_needed():
            data.byteswap(True)
        return data[slice2]

    ############################################################################
    # Properties definition for header, data, header_keys
    ############################################################################

    def getNbFrames(self):
        """
        Getter for number of frames
        """
        return len(self._frames)

    def setNbFrames(self, val):
        """
        Setter for number of frames ... should do nothing. Here just to avoid bugs
        """
        if val != len(self._frames):
            logger.warning("trying to set the number of frames ")
    nframes = property(getNbFrames, setNbFrames, "property: number of frames in EDF file")

    def getHeader(self):
        """
        Getter for the headers. used by the property header,
        """
        return self._frames[self.currentframe].header

    def setHeader(self, _dictHeader):
        """
        Enforces the propagation of the header to the list of frames
        """
        try:
            self._frames[self.currentframe].header = _dictHeader
        except AttributeError:
            self._frames = [Frame(header=_dictHeader)]
        except IndexError:
            if self.currentframe < len(self._frames):
                self._frames.append(Frame(header=_dictHeader))

    def delHeader(self):
        """
        Deleter for edf header
        """
        self._frames[self.currentframe].header = {}

    header = property(getHeader, setHeader, delHeader, "property: header of EDF file")

    def getData(self):
        """
        getter for edf Data
        :return: data for current frame
        :rtype: numpy.ndarray
        """
        npaData = None
        try:
            npaData = self._frames[self.currentframe].data
        except AttributeError:
            self._frames = [Frame()]
            npaData = self._frames[self.currentframe].data
        except IndexError:
            if self.currentframe < len(self._frames):
                self._frames.append(Frame())
                npaData = self._frames[self.currentframe].data
        return npaData

    def setData(self, _data):
        """
        Enforces the propagation of the data to the list of frames
        :param _data: numpy array representing data
        """
        try:
            self._frames[self.currentframe].data = _data
        except AttributeError:
            self._frames = [Frame(data=_data)]
        except IndexError:
            if self.currentframe < len(self._frames):
                self._frames.append(Frame(data=_data))

    def delData(self):
        """
        deleter for edf Data
        """
        self._frames[self.currentframe].data = None

    data = property(getData, setData, delData, "property: data of EDF file")

    def getDim1(self):
        return self._frames[self.currentframe].dim1

    def setDim1(self, _iVal):
        try:
            self._frames[self.currentframe].dim1 = _iVal
        except AttributeError:
            self._frames = [Frame()]
        except IndexError:
            if self.currentframe < len(self._frames):
                self._frames.append(Frame())
                self._frames[self.currentframe].dim1 = _iVal
    dim1 = property(getDim1, setDim1)

    def getDim2(self):
        return self._frames[self.currentframe].dim2

    def setDim2(self, _iVal):
        try:
            self._frames[self.currentframe].dim2 = _iVal
        except AttributeError:
            self._frames = [Frame()]
        except IndexError:
            if self.currentframe < len(self._frames):
                self._frames.append(Frame())
                self._frames[self.currentframe].dim2 = _iVal
    dim2 = property(getDim2, setDim2)

    def getDims(self):
        return self._frames[self.currentframe].dims
    dims = property(getDims)

    def getByteCode(self):
        return self._frames[self.currentframe].bytecode

    def setByteCode(self, _iVal):
        try:
            self._frames[self.currentframe].bytecode = _iVal
        except AttributeError:
            self._frames = [Frame()]
        except IndexError:
            if self.currentframe < len(self._frames):
                self._frames.append(Frame())
                self._frames[self.currentframe].bytecode = _iVal
    bytecode = property(getByteCode, setByteCode)

    def getBpp(self):
        return self._frames[self.currentframe].bpp

    def setBpp(self, _iVal):
        try:
            self._frames[self.currentframe].bpp = _iVal
        except AttributeError:
            self._frames = [Frame()]
        except IndexError:
            if self.currentframe < len(self._frames):
                self._frames.append(Frame())
                self._frames[self.currentframe].bpp = _iVal
    bpp = property(getBpp, setBpp)

    def isIncompleteData(self):
        return self._frames[self.currentframe].incomplete_data

    incomplete_data = property(isIncompleteData)

    @classmethod
    def lazy_iterator(cls, filename):
        """Iterates over the frames of an EDF multi-frame file.

        This function optimizes sequential access to multi-frame EDF files
        by avoiding to read the whole file at first in order to get the number
        of frames and build an index of frames for faster random access.

        Usage:

        >>> from fabio.edfimage import EdfImage

        >>> for frame in EdfImage.lazy_iterator("multiframe.edf"):
        ...     print('Header:', frame.header)
        ...     print('Data:', frame.data)

        :param str filename: File name of the EDF file to read
        :yield: frames one after the other
        """
        edf = cls()
        infile = edf._open(filename, 'rb')

        index = 0

        while True:
            try:
                block = cls._readHeaderBlock(infile, index)
            except MalformedHeaderError:
                logger.debug("Backtrace", exc_info=True)
                if index == 0:
                    infile.close()
                    raise IOError("Invalid first header")
                break

            if block is None:
                # end of file
                if index == 0:
                    infile.close()
                    raise IOError("Empty file")
                break

            frame = Frame(number=index)
            size = frame.parseheader(block)
            frame.file = infile
            frame.start = infile.tell()
            frame.size = size

            try:
                # read data
                frame.getData()
            except Exception as error:
                if isinstance(infile, fabioutils.GzipFile):
                    if compression_module.is_incomplete_gz_block_exception(error):
                        frame.incomplete_data = True
                        break
                logger.warning("infile is %s" % infile)
                logger.warning("Position is %s" % infile.tell())
                logger.warning("size is %s" % size)
                logger.error("It seams this error occurs under windows when reading a (large-) file over network: %s ", error)
                infile.close()
                raise Exception(error)

            frame._check_header_mandatory_keys(filename=filename)
            yield frame
            index += 1

        infile.close()


edfimage = EdfImage
