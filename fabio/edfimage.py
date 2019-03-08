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

from __future__ import with_statement, print_function, absolute_import, division

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

import os
import re
import string
import logging
import numpy

logger = logging.getLogger(__name__)

from . import fabioimage
from .fabioutils import isAscii, toAscii, nice_int, OrderedDict
from .compression import decBzip2, decGzip, decZlib
from . import compression as compression_module
from . import fabioutils
from .utils import deprecation


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


class EdfFrame(fabioimage.FabioFrame):
    """
    A class representing a single frame in an EDF file
    """
    def __init__(self, data=None, header=None, number=None):
        header = EdfImage.check_header(header)
        super(EdfFrame, self).__init__(data, header=header)

        self._data_compression = None
        self._data_swap_needed = None
        self._data = data
        self.start = None
        """Position of start of raw data in file"""
        self.size = None
        """Size of raw data block in file (including padding)"""
        self._data_size = None
        """Size of the util raw data if different than `size` (without padding)"""
        self.file = None
        """Opened file object with locking capabilities"""
        self._dtype = None
        self.incomplete_data = False

        if number is not None:
            deprecation.deprecated_warning(reason="Argument 'number' is not used anymore", deprecated_since="0.10.0beta")

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
        shape = []

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
                shape.insert(0, dim1)
        else:
            logger.error("No Dim_1 in headers !!!")
        if "DIM_2" in capsHeader:
            try:
                dim2 = nice_int(self.header[capsHeader['DIM_2']])
            except ValueError:
                logger.error("Unable to convert to integer Dim_2: %s %s" % (capsHeader["DIM_2"], self.header[capsHeader["DIM_2"]]))
            else:
                calcsize *= dim2
                shape.insert(0, dim2)
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
                        shape.insert(0, dim3)
                    iDim += 1

            else:
                logger.debug("No Dim_3 -> it is a 2D image")
                iDim = None
        shape = tuple(shape)
        self._shape = shape

        if self._dtype is None:
            if "DATATYPE" in capsHeader:
                bytecode = DATA_TYPES[self.header[capsHeader['DATATYPE']]]
            else:
                bytecode = numpy.uint16
                logger.warning("Defaulting type to uint16")
            self._dtype = numpy.dtype(bytecode)

        if "COMPRESSION" in capsHeader:
            self._data_compression = self.header[capsHeader["COMPRESSION"]].upper()
            if self._data_compression == "NONE":
                self._data_compression = None
            elif self._data_compression.startswith("NO"):
                self._data_compression = None
        else:
            self._data_compression = None

        bpp = self._dtype.itemsize
        calcsize *= bpp

        if (self.size is None):
            self.size = calcsize
        elif self._data_compression is None:
            if self.size < calcsize:
                logger.warning("Malformed file. The specified size of the data block is smaller than the expected size (%i < %i). Size is set to the the calculated one. This frame (and following) could be broken.", self.size, calcsize)
                self.size = calcsize
            elif self.size > calcsize:
                # The data block is padded, store here the real data size
                self._data_size = calcsize

        byte_order = self.header[capsHeader['BYTEORDER']]
        if ('Low' in byte_order and numpy.little_endian) or \
           ('High' in byte_order and not numpy.little_endian):
            self._data_swap_needed = False
        if ('High' in byte_order and numpy.little_endian) or \
           ('Low' in byte_order and not numpy.little_endian):
            if bpp in [2, 4, 8]:
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
            msg = "EDF file %s%s misses mandatory keys: %s "
            if self.index is not None:
                frame = " (frame %i)" % self.index
            else:
                frame = ""
            logger.info(msg, filename, frame, " ".join(missing))
        return len(missing) == 0

    def swap_needed(self):
        """
        Decide if we need to byteswap
        """
        return self._data_swap_needed

    def _unpack(self):
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
            if self._dtype is None:
                assert(False)
            shape = self.shape
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
                                return numpy.zeros(shape)
                        raise e

            if self._data_compression is not None:
                compression = self._data_compression
                uncompressed_size = self._dtype.itemsize
                for i in shape:
                    uncompressed_size *= i
                if "OFFSET" in compression:
                    try:
                        import byte_offset  # IGNORE:F0401
                    except ImportError as error:
                        logger.error("Unimplemented compression scheme:  %s (%s)" % (compression, error))
                    else:
                        myData = byte_offset.analyseCython(fileData, size=uncompressed_size)
                        rawData = myData.astype(self._dtype).tostring()
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
            if self._data_size is not None:
                rawData = rawData[0:self._data_size]
            data = numpy.frombuffer(rawData, self._dtype).copy().reshape(shape)
            if self.swap_needed():
                data.byteswap(True)
            self._data = data
            self._dtype = None
        return data

    @property
    def data(self):
        """
        Returns the data after unpacking it if needed.

        :return: dataset as numpy.ndarray
        """
        return self._unpack()

    @data.setter
    def data(self, value):
        """Setter for data in edf frame"""
        self._data = value

    @deprecation.deprecated(reason="Prefer using 'frame.data'", deprecated_since="0.10.0beta")
    def getData(self):
        """
        Returns the data after unpacking it if needed.

        :return: dataset as numpy.ndarray
        """
        return self.data

    @deprecation.deprecated(reason="Prefer using 'frame.data ='", deprecated_since="0.10.0beta")
    def setData(self, npa=None):
        """Setter for data in edf frame"""
        self._data = npa

    def get_edf_block(self, force_type=None, fit2dMode=False):
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
        header["HeaderID"] = "EH:%06d:000000:000000" % (self.index + fit2dMode)
        header_keys.insert(0, "Image")
        header["Image"] = str(self.index + fit2dMode)

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
            header["EDF_DataBlockID"] = "%i.Image.Psd" % (self.index + fit2dMode)
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

    @deprecation.deprecated(reason="Prefer using 'getEdfBlock'", deprecated_since="0.10.0beta")
    def getEdfBlock(self, force_type=None, fit2dMode=False):
        return self.get_edf_block(force_type, fit2dMode)

    @property
    @deprecation.deprecated(reason="Prefer using 'index'", deprecated_since="0.10.0beta")
    def iFrame(self):
        """Returns the frame index of this frame"""
        return self._index


class EdfImage(fabioimage.FabioImage):
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

        fabioimage.FabioImage.__init__(self, stored_data, header)

        if frames is None:
            frame = EdfFrame(data=self.data, header=self.header)
            self._frames = [frame]
        else:
            self._frames = frames

    def _get_frame(self, num):
        if self._frames is None:
            return IndexError("No frames available")
        frame = self._frames[num]
        frame._set_container(self, num)
        frame._set_file_container(self, num)
        return frame

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
    def _read_header_block(infile, frame_id):
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
                block = self._read_header_block(infile, len(self._frames))
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

            frame = EdfFrame()
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
            newImage = fabioimage.FabioImage.getframe(self, num)
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
            newImage = fabioimage.FabioImage.previous(self)
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
            newImage = fabioimage.FabioImage.next(self)
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
                frame._set_container(self, i)
                outfile.write(frame.get_edf_block(force_type=force_type, fit2dMode=fit2dMode))

    def append_frame(self, frame=None, data=None, header=None):
        """
        Method used add a frame to an EDF file
        :param frame: frame to append to edf image
        :type frame: instance of Frame
        """
        if isinstance(frame, EdfFrame):
            self._frames.append(frame)
        elif hasattr(frame, "header") and hasattr(frame, "data"):
            self._frames.append(EdfFrame(frame.data, frame.header))
        else:
            self._frames.append(EdfFrame(data, header))

    @deprecation.deprecated(reason="Prefer using 'append_frame'", deprecated_since="0.10.0beta")
    def appendFrame(self, frame=None, data=None, header=None):
        self.append_frame(frame, data, header)

    def delete_frame(self, frameNb=None):
        """
        Method used to remove a frame from an EDF image. by default the last one is removed.
        :param int frameNb: frame number to remove, by  default the last.
        """
        if frameNb is None:
            self._frames.pop()
        else:
            self._frames.pop(frameNb)

    @deprecation.deprecated(reason="Prefer using 'delete_frame'", deprecated_since="0.10.0beta")
    def deleteFrame(self, frameNb=None):
        self.delete_frame(frameNb)

    def fast_read_data(self, filename=None):
        """
        This is a special method that will read and return the data from another file ...
        The aim is performances, ... but only supports uncompressed files.

        :return: data from another file using positions from current EdfImage
        """
        if (filename is None) or not os.path.isfile(filename):
            raise RuntimeError("EdfImage.fast_read_data is only valid with another file: %s does not exist" % (filename))
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

    @deprecation.deprecated(reason="Prefer using 'fastReadData'", deprecated_since="0.10.0beta")
    def fastReadData(self, filename):
        return self.fast_read_data(filename)

    def fast_read_roi(self, filename, coords=None):
        """
        Method reading Region of Interest of another file  based on metadata available in current EdfImage.
        The aim is performances, ... but only supports uncompressed files.

        :return: ROI-data from another file using positions from current EdfImage
        :rtype: numpy 2darray
        """
        if (filename is None) or not os.path.isfile(filename):
            raise RuntimeError("EdfImage.fast_read_roi is only valid with another file: %s does not exist" % (filename))
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

    @deprecation.deprecated(reason="Prefer using 'fast_read_roi'", deprecated_since="0.10.0beta")
    def fastReadROI(self, filename, coords=None):
        return self.fast_read_roi(filename, coords)

    ############################################################################
    # Properties definition for header, data, header_keys
    ############################################################################

    def _get_any_frame(self):
        """Returns the current if available, else create and return a new empty
        frame."""
        try:
            return self._frames[self.currentframe]
        except AttributeError:
            frame = EdfFrame()
            self._frames = [frame]
            return frame
        except IndexError:
            if self.currentframe < len(self._frames):
                frame = EdfFrame()
                self._frames.append(frame)
                return frame
            raise

    @property
    def nframes(self):
        """Returns the number of frames contained in this file

        :rtype: int
        """
        return len(self._frames)

    @deprecation.deprecated(reason="Prefer using 'img.nframes'", deprecated_since="0.10.0beta")
    def getNbFrames(self):
        """
        Getter for number of frames
        """
        return len(self._frames)

    @deprecation.deprecated(reason="This call to 'setNbFrames' does nothing and should be removed", deprecated_since="0.10.0beta")
    def setNbFrames(self, val):
        """
        Setter for number of frames ... should do nothing. Here just to avoid bugs
        """
        if val != len(self._frames):
            logger.warning("Setting the number of frames is not allowed.")

    @property
    def header(self):
        frame = self._get_any_frame()
        return frame.header

    @header.setter
    def header(self, value):
        frame = self._get_any_frame()
        frame.header = value

    @header.deleter
    def header(self):
        frame = self._get_any_frame()
        frame.header = None

    @deprecation.deprecated(reason="Prefer using 'img.header'", deprecated_since="0.10.0beta")
    def getHeader(self):
        """
        Getter for the headers. used by the property header,
        """
        return self._frames[self.currentframe].header

    @deprecation.deprecated(reason="Prefer using 'img.header ='", deprecated_since="0.10.0beta")
    def setHeader(self, _dictHeader):
        """
        Enforces the propagation of the header to the list of frames
        """
        frame = self._get_any_frame()
        frame.header = _dictHeader

    @deprecation.deprecated(reason="Prefer using 'del img.header'", deprecated_since="0.10.0beta")
    def delHeader(self):
        """
        Deleter for edf header
        """
        self._frames[self.currentframe].header = {}

    @property
    def shape(self):
        frame = self._get_any_frame()
        return frame.shape

    @property
    def dtype(self):
        frame = self._get_any_frame()
        return frame.dtype

    @property
    def data(self):
        frame = self._get_any_frame()
        return frame.data

    @data.setter
    def data(self, value):
        frame = self._get_any_frame()
        frame.data = value

    @data.deleter
    def data(self):
        frame = self._get_any_frame()
        frame.data = None

    @deprecation.deprecated(reason="Prefer using 'img.data'", deprecated_since="0.10.0beta")
    def getData(self):
        """
        getter for edf Data
        :return: data for current frame
        :rtype: numpy.ndarray
        """
        return self.data

    @deprecation.deprecated(reason="Prefer using 'img.data ='", deprecated_since="0.10.0beta")
    def setData(self, _data=None):
        """
        Enforces the propagation of the data to the list of frames
        :param data: numpy array representing data
        """
        frame = self._get_any_frame()
        frame.data = _data

    @deprecation.deprecated(reason="Prefer using 'del img.data'", deprecated_since="0.10.0beta")
    def delData(self):
        """
        deleter for edf Data
        """
        self._frames[self.currentframe].data = None

    @deprecation.deprecated(reason="Prefer using 'dim1'", deprecated_since="0.10.0beta")
    def getDim1(self):
        return self.dim1

    @deprecation.deprecated(reason="Setting dim1 is not anymore allowed. If the data is not set use shape instead.", deprecated_since="0.10.0beta")
    def setDim1(self, _iVal=None):
        frame = self._get_any_frame()
        frame.dim1 = _iVal

    @property
    def dim1(self):
        return self._frames[self.currentframe].dim1

    @deprecation.deprecated(reason="Prefer using 'dim2'", deprecated_since="0.10.0beta")
    def getDim2(self):
        return self._frames[self.currentframe].dim2

    @deprecation.deprecated(reason="Setting dim2 is not anymore allowed. If the data is not set use shape instead.", deprecated_since="0.10.0beta")
    def setDim2(self, _iVal=None):
        frame = self._get_any_frame()
        frame.dim2 = _iVal

    @property
    def dim2(self):
        return self._frames[self.currentframe].dim2

    @deprecation.deprecated(reason="Prefer using 'dims'", deprecated_since="0.10.0beta")
    def getDims(self):
        return self._frames[self.currentframe].dims

    @property
    def dims(self):
        return self._frames[self.currentframe].dims

    @deprecation.deprecated(reason="Prefer using 'bytecode'", deprecated_since="0.10.0beta")
    def getByteCode(self):
        return self.bytecode

    @deprecation.deprecated(reason="Setting bytecode is not anymore allowed. If the data is not set use dtype instead.", deprecated_since="0.10.0beta")
    def setByteCode(self, iVal=None, _iVal=None):
        raise NotImplementedError("No more implemented")

    @property
    def bytecode(self):
        return self._frames[self.currentframe].bytecode

    @deprecation.deprecated(reason="Prefer using 'bpp'", deprecated_since="0.10.0beta")
    def getBpp(self):
        return self._frames[self.currentframe].bpp

    @deprecation.deprecated(reason="Setting bpp is not anymore allowed. If the data is not set use dtype instead.", deprecated_since="0.10.0beta")
    def setBpp(self, iVal=None, _iVal=None):
        raise NotImplementedError("No more implemented")

    @property
    def bpp(self):
        return self._frames[self.currentframe].bpp

    @deprecation.deprecated(reason="Prefer using 'incomplete_data'", deprecated_since="0.10.0beta")
    def isIncompleteData(self):
        return self.incomplete_data

    @property
    def incomplete_data(self):
        return self._frames[self.currentframe].incomplete_data

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
                block = cls._read_header_block(infile, index)
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

            frame = EdfFrame()
            frame._set_container(edf, index)
            frame._set_file_container(edf, index)
            size = frame.parseheader(block)
            frame.file = infile
            frame.start = infile.tell()
            frame.size = size

            try:
                # read data
                frame._unpack()
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


Frame = EdfFrame
"""Compatibility code with fabio <= 0.8"""

edfimage = EdfImage
