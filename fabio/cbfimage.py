# coding: utf-8
#
#    Project: FabIO X-ray image reader
#
#    Copyright (C) 2010-2023 European Synchrotron Radiation Facility
#                       Grenoble, France
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

"""
Authors: Jérôme Kieffer, ESRF
         email:jerome.kieffer@esrf.fr

Cif Binary Files images are 2D images written by the Pilatus detector and others.
They use a modified (simplified) byte-offset algorithm.

CIF is a library for manipulating Crystallographic information files and tries
to conform to the specification of the IUCR
"""

__author__ = "Jérôme Kieffer"
__contact__ = "jerome.kieffer@esrf.eu"
__license__ = "MIT"
__date__ = "14/04/2023"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"

import os
import logging
import numpy
from collections import OrderedDict
from typing import NamedTuple

from .fabioimage import FabioImage
from .compression import compByteOffset, decByteOffset, md5sum
from .ext._cif import split_tokens
from . import version, date
logger = logging.getLogger(__name__)
__version__ = ["##CBF: VERSION 1.5, FabIO version %s (%s) - %s" % (version, date, __copyright__)]

DATA_TYPES = {"signed 8-bit integer": "int8",
              "signed 16-bit integer": "int16",
              "signed 32-bit integer": "int32",
              "signed 64-bit integer": "int64",
              "unsigned 8-bit integer": "uint8",
              "unsigned 16-bit integer": "uint16",
              "unsigned 32-bit integer": "uint32",
              "unsigned 64-bit integer": "uint64"
              }

MINIMUM_KEYS = ["X-Binary-Size-Fastest-Dimension",
                "X-Binary-Size-Second-Dimension",
                "X-Binary-Size",
                "X-Binary-Number-of-Elements",
                'X-Binary-Element-Type',
                'X-Binary-Number-of-Elements']


class CbfImage(FabioImage):
    """
    Read the Cif Binary File data format
    """

    DESCRIPTION = "Cif Binary Files format (used by the Pilatus detectors and others)"

    DEFAULT_EXTENSIONS = ["cbf"]

    STARTER = b"\x0c\x1a\x04\xd5"
    PADDING = 512
    BINARAY_SECTION = b"--CIF-BINARY-FORMAT-SECTION--"
    CIF_BINARY_BLOCK_KEY = "_array_data.data"

    def __init__(self, data=None, header=None, fname=None):
        """
        Constructor of the class CIF Binary File reader.

        :param str fname: the name of the file to open
        """
        FabioImage.__init__(self, data, header)
        self.cif = CIF()
        self.pilatus_headers = None
        self.cbs = None
        self.start_binary = None
        if fname is not None:  # load the file)
            self.read(fname)

    @staticmethod
    def checkData(data=None):
        if data is None:
            return None
        elif numpy.issubdtype(data.dtype, int):
            return data
        else:
            return data.astype(int)

    def _readheader(self, inStream):
        """
        Read in a header in some CBF format from a string representing binary stuff

        :param file inStream: file containing the Cif Binary part.
        """
        self._read_cif_header(inStream)
        self._read_binary_section_header(inStream)

    def _read_cif_header(self, inStream):
        """Read in a ASCII CIF header

        :param inStream: file containing the Cif Binary part.
        :type inStream: opened file.
        """
        blocks = []
        last = ""
        header_data = None
        for i in range(16):
            # up to 512*16 = 8k headers
            ablock = inStream.read(self.PADDING)
            blocks.append(ablock)
            if last:
                extra = len(self.BINARAY_SECTION)
                extblock = last[-extra:] + ablock
            else:
                extra = 0
                extblock = ablock
            res = extblock.find(self.BINARAY_SECTION)
            if res >= 0:
                start_cbs = i * self.PADDING - extra + res
                all_blocks = b"".join(blocks)
                header_data = all_blocks[:start_cbs] + b"CIF Binary Section\n;\n"
                self.cbs = all_blocks[start_cbs:]
                break
            last = ablock
        else:
            header_data = b"".join(blocks) + inStream.read()
        self.cif._parseCIF(header_data)

        # backport contents of the CIF data to the headers
        for key, value in self.cif.items():
            if key == self.CIF_BINARY_BLOCK_KEY:
                if self.cbs is None:
                    self.cbs = value
            else:
                if isinstance(value, str):
                    value = value.strip(" \"\n\r\t")
                self.header[key] = value
        if self.header.get("_array_data.header_convention") == "PILATUS_1.2":
            self.pilatus_headers = PilatusHeader(self.header.get("_array_data.header_contents", ""))

    def _read_binary_section_header(self, inStream):
        """
        Read the binary section header
        """
        self.start_binary = self.cbs.find(self.STARTER)
        while self.start_binary < 0:
            self.cbs += inStream.read(self.PADDING)
            self.start_binary = self.cbs.find(self.STARTER)
        bin_headers = self.cbs[:self.start_binary]
        lines = bin_headers.split(b"\n")
        for line in lines[1:]:
            if len(line) < 10:
                break
            try:
                key, val = line.split(b':', 1)
            except ValueError:
                key, val = line.split(b'=', 1)
            key = key.strip().decode("ASCII")
            self.header[key] = val.strip(b" \"\n\r\t").decode("ASCII")
        missing = []
        for item in MINIMUM_KEYS:
            if item not in self.header:
                missing.append(item)
        if missing:
            logger.info("Mandatory keys missing in CBF file: " + ", ".join(missing))
        # Compute image size
        try:
            slow = int(self.header['X-Binary-Size-Fastest-Dimension'])
            fast = int(self.header['X-Binary-Size-Second-Dimension'])
            self._shape = fast, slow
        except (KeyError, ValueError):
            raise IOError("CBF file %s is corrupt, no dimensions in it" % inStream.name)
        try:
            bytecode = DATA_TYPES[self.header['X-Binary-Element-Type']]
        except KeyError:
            bytecode = "int32"
            logger.warning("Defaulting type to int32")
        self._dtype = numpy.dtype(bytecode)

    def read_raw_data(self, infile):
        """Read and return the raw data chunk

        :param infile: opened file at correct position
        :return: raw compressed stream
        """
        if self.CIF_BINARY_BLOCK_KEY not in self.cif:
            err = "Not key %s in CIF, no CBF image in %s" % (self.CIF_BINARY_BLOCK_KEY, self.filename)
            logger.error(err)
            for kv in self.cif.items():
                logger.debug("%s: %s", kv)
            raise RuntimeError(err)
        if self.cif[self.CIF_BINARY_BLOCK_KEY] == "CIF Binary Section":
            size = len(self.STARTER) + int(self.header["X-Binary-Size"]) - len(self.cbs) + self.start_binary
            if size > 0:
                self.cbs += infile.read(size)
            elif size < 0:
                self.cbs = self.cbs[:size]
        else:
            if len(self.cif[self.CIF_BINARY_BLOCK_KEY]) > int(self.header["X-Binary-Size"]) + self.start_binary + len(self.STARTER):
                self.cbs = self.cif[self.CIF_BINARY_BLOCK_KEY][:int(self.header["X-Binary-Size"]) + self.start_binary + len(self.STARTER)]
            else:
                self.cbs = self.cif[self.CIF_BINARY_BLOCK_KEY]
        return self.cbs[self.start_binary + len(self.STARTER):]

    def read(self, fname, frame=None, check_MD5=True, only_raw=False):
        """Read in header into self.header and the data   into self.data

        :param str fname: name of the file
        :return: fabioimage instance
        """
        self.filename = fname
        self.header = self.check_header()
        self.resetvals()

        infile = self._open(fname, "rb")
        self._readheader(infile)

        logger.debug("CBS type %s len %s" % (type(self.cbs), len(self.cbs)))

        binary_data = self.read_raw_data(infile)
        if only_raw:
            return binary_data

        if ("Content-MD5" in self.header) and check_MD5:
                ref = numpy.string_(self.header["Content-MD5"])
                obt = md5sum(binary_data)
                if ref != obt:
                    logger.error("Checksum of binary data mismatch: expected %s, got %s" % (ref, obt))

        if self.header["conversions"] == "x-CBF_BYTE_OFFSET":
            data = numpy.ascontiguousarray(self._readbinary_byte_offset(binary_data,), self._dtype)
            data.shape = self._shape
            self.data = data
            self._shape = None
            self._dtype = None
        else:
            raise Exception(IOError, "Compression scheme not yet supported, please contact the author")

        self.resetvals()
        return self

    def _readbinary_byte_offset(self, raw_bytes):
        """
        Read in a binary part of an x-CBF_BYTE_OFFSET compressed image

        :param str inStream: the binary image (without any CIF decorators)
        :return: a linear numpy array without shape and dtype set
        :rtype: numpy array
        """
        dim2, dim1 = self._shape
        data = decByteOffset(raw_bytes, size=dim1 * dim2, dtype=self._dtype)
        assert len(data) == dim1 * dim2
        return data

    def write(self, fname):
        """
        write the file in CBF format
        :param str fname: name of the file
        """
        if self.data is None:
            raise RuntimeError("CBF image contains no data")
        # The shape is provided by self.data
        self._shape = None
        dim2, dim1 = self.shape
        binary_blob = compByteOffset(self.data)
        dtype = "Unknown"
        for key, value in DATA_TYPES.items():
            if value == self.data.dtype:
                dtype = key
        binary_block = [b"--CIF-BINARY-FORMAT-SECTION--",
                        b"Content-Type: application/octet-stream;",
                        b'     conversions="x-CBF_BYTE_OFFSET"',
                        b'Content-Transfer-Encoding: BINARY',
                        numpy.string_("X-Binary-Size: %d" % (len(binary_blob))),
                        b"X-Binary-ID: 1",
                        numpy.string_('X-Binary-Element-Type: "%s"' % (dtype)),
                        b"X-Binary-Element-Byte-Order: LITTLE_ENDIAN",
                        b"Content-MD5: " + md5sum(binary_blob),
                        numpy.string_("X-Binary-Number-of-Elements: %d" % (dim1 * dim2)),
                        numpy.string_("X-Binary-Size-Fastest-Dimension: %d" % dim1),
                        numpy.string_("X-Binary-Size-Second-Dimension: %d" % dim2),
                        b"X-Binary-Size-Padding: 1",
                        b"",
                        self.STARTER + binary_blob,
                        b"",
                        b"--CIF-BINARY-FORMAT-SECTION----"]

        if "_array_data.header_contents" not in self.header:
            nonCifHeaders = []
        else:
            nonCifHeaders = [i.strip()[2:] for i in self.header["_array_data.header_contents"].split("\n") if i.find("# ") >= 0]

        for key in self.header:
            if key.startswith("_"):
                if key not in self.cif or self.cif[key] != self.header[key]:
                    self.cif[key] = self.header[key]
            elif key.startswith("X-Binary-"):
                pass
            elif key.startswith("Content-"):
                pass
            elif key.startswith("conversions"):
                pass
            elif key.startswith("filename"):
                pass
            elif key in self.header:
                nonCifHeaders.append("%s %s" % (key, self.header[key]))
        if self.pilatus_headers is not None:
            # regenerate  the Pilatus header and set the convention
            self.cif["_array_data.header_contents"] = str(self.pilatus_headers)
            self.cif["_array_data.header_convention"] = "PILATUS_1.2"

        if len(nonCifHeaders) > 0:
            self.cif["_array_data.header_contents"] = "\r\n".join(["# %s" % i for i in nonCifHeaders])

        self.cbf = b"\r\n".join(binary_block)
        block = b"\r\n".join([b"", self.CIF_BINARY_BLOCK_KEY.encode("ASCII"), b";", self.cbf, b";"])
        self.cif.pop(self.CIF_BINARY_BLOCK_KEY, None)
        with open(fname, "wb") as out_file:
            out_file.write(self.cif.tostring(fname, "\r\n").encode("ASCII"))
            out_file.write(block)


################################################################################
# CIF class
################################################################################
class CIF(dict):
    """
    This is the CIF class, it represents the CIF dictionary;
    and as a a python dictionary thus inherits from the dict built in class.

    keys are always unicode (str in python3)
    values are bytes
    """
    EOL = [numpy.string_(i) for i in ("\r", "\n", "\r\n", "\n\r")]
    BLANK = [numpy.string_(i) for i in (" ", "\t")] + EOL
    SINGLE_QUOTE = numpy.string_("'")
    DOUBLE_QUOTE = numpy.string_('"')
    SEMICOLUMN = numpy.string_(';')
    DOT = numpy.string_('.')
    START_COMMENT = (SINGLE_QUOTE, DOUBLE_QUOTE)
    BINARY_MARKER = numpy.string_("--CIF-BINARY-FORMAT-SECTION--")
    HASH = numpy.string_("#")
    LOOP = numpy.string_("loop_")
    UNDERSCORE = ord("_")
    QUESTIONMARK = numpy.string_("?")
    STOP = numpy.string_("stop_")
    GLOBAL = numpy.string_("global_")
    DATA = numpy.string_("data_")
    SAVE = numpy.string_("save_")

    def __init__(self, _strFilename=None):
        """
        Constructor of the class.

        :param _strFilename: the name of the file to open
        :type  _strFilename: filename (str) or file object
        """
        dict.__init__(self)
        self._ordered = []
        if _strFilename is not None:  # load the file)
            self.loadCIF(_strFilename)

    def __setitem__(self, key, value):
        if key not in self._ordered:
            self._ordered.append(key)
        return dict.__setitem__(self, key, value)

    def pop(self, key, default=None):
        if key in self._ordered:
            self._ordered.remove(key)
        return dict.pop(self, key, default)

    def popitem(self, key, default=None):
        if key in self._ordered:
            self._ordered.remove(key)
        return dict.popitem(self, key, None)

    def loadCIF(self, _strFilename, _bKeepComment=False):
        """Load the CIF file and populates the CIF dictionary into the object

        :param str _strFilename: the name of the file to open
        :return: None
        """
        own_fd = False
        if isinstance(_strFilename, (bytes, str)):
            if os.path.isfile(_strFilename):
                infile = open(_strFilename, "rb")
                own_fd = True
            else:
                raise RuntimeError("CIF.loadCIF: No such file to open: %s" % _strFilename)
        elif "read" in dir(_strFilename):
            infile = _strFilename
        else:
            raise RuntimeError("CIF.loadCIF: what is %s type %s" % (_strFilename, type(_strFilename)))
        if _bKeepComment:
            self._parseCIF(numpy.string_(infile.read()))
        else:
            self._parseCIF(CIF._readCIF(infile))
        if own_fd:
            infile.close()

    readCIF = loadCIF

    @staticmethod
    def isAscii(text):
        """
        Check if all characters in a string are ascii,

        :param str text: input string
        :return: boolean
        :rtype: boolean
        """
        try:
            text.decode("ascii")
        except UnicodeDecodeError:
            return False
        else:
            return True

    @classmethod
    def _readCIF(cls, instream):
        """
        - Check if the filename containing the CIF data exists
        - read the cif file
        - removes the comments

        :param file instream: opened file object containing the CIF data
        :return: a set of bytes (8-bit string) containing the raw data
        :rtype: string
        """
        if "read" not in dir(instream):
            raise RuntimeError("CIF._readCIF(instream): I expected instream to be an opened file,\
             here I got %s type %s" % (instream, type(instream)))
        out_bytes = numpy.string_("")
        for sLine in instream:
            nline = numpy.string_(sLine)
            pos = nline.find(cls.HASH)
            if pos >= 0:
                if cls.isAscii(nline):
                    out_bytes += nline[:pos] + numpy.string_(os.linesep)
                if pos > 80:
                    logger.warning("This line is too long and could cause problems in PreQuest: %s", sLine)
            else:
                out_bytes += nline
                if len(sLine.strip()) > 80:
                    logger.warning("This line is too long and could cause problems in PreQuest: %s", sLine)
        return out_bytes

    def _parseCIF(self, bytes_text):
        """
        - Parses the text of a CIF file
        - Cut it in fields
        - Find all the loops and process
        - Find all the keys and values

        :param bytes_text: the content of the CIF - file
        :type bytes_text: 8-bit string (str in python2 or bytes in python3)
        :return: Nothing, the data are incorporated at the CIF object dictionary
        :rtype: None
        """
        loopidx = []
        looplen = []
        loop = []
        fields = split_tokens(bytes_text)

        logger.debug("After split got %s fields of len: %s", len(fields), [len(i) for i in fields])

        for idx, field in enumerate(fields):
            if field.lower() == self.LOOP:
                loopidx.append(idx)
        if loopidx:
            for i in loopidx:
                loopone, length, keys = CIF._analyseOneLoop(fields, i)
                loop.append([keys, loopone])
                looplen.append(length)

            for i in range(len(loopidx) - 1, -1, -1):
                f1 = fields[:loopidx[i]] + fields[loopidx[i] + looplen[i]:]
                fields = f1

            self[self.LOOP.decode("ASCII")] = loop

        for i in range(len(fields) - 1):
            if len(fields[i + 1]) == 0:
                fields[i + 1] = self.QUESTIONMARK
            if fields[i][0] == self.UNDERSCORE and fields[i + 1][0] != self.UNDERSCORE:
                try:
                    data = fields[i + 1].decode("ASCII")
                except UnicodeError:
                    logger.warning("Unable to decode in ascii: %s" % fields[i + 1])
                    data = fields[i + 1]
                self[(fields[i]).decode("ASCII")] = data

    @classmethod
    def _splitCIF(cls, bytes_text):
        """
        Separate the text in fields as defined in the CIF

        :param bytes_text: the content of the CIF - file
        :type bytes_text:  8-bit string (str in python2 or bytes in python3)
        :return: list of all the fields of the CIF
        :rtype: list
        """
        fields = []
        while True:
            if len(bytes_text) == 0:
                break
            elif bytes_text[0] == cls.SINGLE_QUOTE:
                idx = 0
                finished = False
                while not finished:
                    idx += 1 + bytes_text[idx + 1:].find(cls.SINGLE_QUOTE)
                    if idx >= len(bytes_text) - 1:
                        fields.append(bytes_text[1:-1].strip())
                        bytes_text = numpy.string_("")
                        finished = True
                        break

                    if bytes_text[idx + 1] in cls.BLANK:
                        fields.append(bytes_text[1:idx].strip())
                        tmp_text = bytes_text[idx + 1:]
                        bytes_text = tmp_text.strip()
                        finished = True

            elif bytes_text[0] == cls.DOUBLE_QUOTE:
                idx = 0
                finished = False
                while not finished:
                    idx += 1 + bytes_text[idx + 1:].find(cls.DOUBLE_QUOTE)
                    if idx >= len(bytes_text) - 1:
                        fields.append(bytes_text[1:-1].strip())
                        bytes_text = numpy.string_("")
                        finished = True
                        break

                    if bytes_text[idx + 1] in cls.BLANK:
                        fields.append(bytes_text[1:idx].strip())
                        tmp_text = bytes_text[idx + 1:]
                        bytes_text = tmp_text.strip()
                        finished = True

            elif bytes_text[0] == cls.SEMICOLUMN:
                if bytes_text[1:].strip().find(cls.BINARY_MARKER) == 0:
                    idx = bytes_text[32:].find(cls.BINARY_MARKER)
                    if idx == -1:
                        idx = 0
                    else:
                        idx += 32 + len(cls.BINARY_MARKER)
                else:
                    idx = 0
                finished = False
                while not finished:
                    idx += 1 + bytes_text[idx + 1:].find(cls.SEMICOLUMN)
                    if bytes_text[idx - 1] in cls.EOL:
                        fields.append(bytes_text[1:idx - 1].strip())
                        tmp_text = bytes_text[idx + 1:]
                        bytes_text = tmp_text.strip()
                        finished = True
            else:
                res = bytes_text.split(None, 1)
                if len(res) == 2:
                    first, second = bytes_text.split(None, 1)
                    if cls.isAscii(first):
                        fields.append(first)
                        bytes_text = second.strip()
                        continue
                start_binary = bytes_text.find(cls.BINARY_MARKER)
                if start_binary > 0:
                    end_binary = bytes_text[start_binary + 1:].find(cls.BINARY_MARKER) + start_binary + 1 + len(cls.BINARY_MARKER)
                    fields.append(bytes_text[:end_binary])
                    bytes_text = bytes_text[end_binary:].strip()
                else:
                    fields.append(bytes_text)
                    bytes_text = numpy.string_("")
                    break
        return fields

    @classmethod
    def _analyseOneLoop(cls, fields, start_idx):
        """Processes one loop in the data extraction of the CIF file
        :param list fields: list of all the words contained in the cif file
        :param int start_idx: the starting index corresponding to the "loop_" key
        :return: the list of loop dictionaries, the length of the data
            extracted from the fields and the list of all the keys of the loop.
        :rtype: tuple
        """
        loop = []
        keys = []
        i = start_idx + 1
        finished = False
        while not finished:
            if fields[i][0] == cls.UNDERSCORE:
                keys.append(fields[i])
                i += 1
            else:
                finished = True
        data = []
        while True:
            if i >= len(fields):
                break
            elif len(fields[i]) == 0:
                break
            elif fields[i][0] == cls.UNDERSCORE:
                break
            elif fields[i] in (cls.LOOP, cls.STOP, cls.GLOBAL, cls.DATA, cls.SAVE):
                break
            else:
                data.append(fields[i])
                i += 1
        k = 0

        if len(data) < len(keys):
            element = {}
            for j in keys:
                if k < len(data):
                    element[j] = data[k]
                else:
                    element[j] = cls.QUESTIONMARK
                k += 1
            loop.append(element)

        else:
            for i in range(len(data) // len(keys)):
                element = {}
                for j in keys:
                    element[j] = data[k]
                    k += 1
                loop.append(element)
        return loop, 1 + len(keys) + len(data), keys

##########################################
# everything needed to  write a CIF file #
##########################################
    def saveCIF(self, _strFilename="test.cif", linesep=os.linesep, binary=False):
        """Transforms the CIF object in string then write it into the given file
        :param _strFilename: the of the file to be written
        :param linesep: line separation used (to force compatibility with windows/unix)
        :param binary: Shall we write the data as binary (True only for imageCIF/CBF)
        :return: None
        """
        if binary:
            mode = "wb"
        else:
            mode = "w"
        with open(_strFilename, mode) as fFile:
            fFile.write(self.tostring(_strFilename, linesep))

    def tostring(self, _strFilename=None, linesep=os.linesep):
        """
        Converts a cif dictionnary to a string according to the CIF syntax.

        :param str _strFilename: the name of the filename to be appended in the
            header of the CIF file.
        :param linesep: default line separation (can be '\\n' or '\\r\\n').
        :return: a string that corresponds to the content of the CIF-file.
        """
        lstStrCif = ["#" + i for i in __version__]
        if "_chemical_name_common" in self:
            t = self["_chemical_name_common"].split()[0]
        elif _strFilename is not None:
            t = os.path.splitext(os.path.split(str(_strFilename).strip())[1])[0]
        else:
            t = ""
        lstStrCif.append("data_%s" % (t))
        # first of all get all the keys:
        lKeys = list(self.keys())
        lKeys.sort()
        for key in lKeys[:]:
            if key in self._ordered:
                lKeys.remove(key)
        self._ordered += lKeys

        for sKey in self._ordered:
            if sKey == "loop_":
                continue
            if sKey not in self:
                self._ordered.remove(sKey)
                logger.debug("Skipping key %s from ordered list as no more present in dict")
                continue
            sValue = str(self[sKey])
            if sValue.find("\n") > -1:  # should add value  between ;;
                lLine = [sKey, ";", sValue, ";", ""]
            elif len(sValue.split()) > 1:  # should add value between ''
                sLine = "%s        '%s'" % (sKey, sValue)
                if len(sLine) > 80:
                    lLine = [str(sKey), sValue]
                else:
                    lLine = [sLine]
            else:
                sLine = "%s        %s" % (sKey, sValue)
                if len(sLine) > 80:
                    lLine = [str(sKey), sValue]
                else:
                    lLine = [sLine]
            lstStrCif += lLine
        if "loop_" in self:
            for loop in self["loop_"]:
                lstStrCif.append("loop_ ")
                lKeys = loop[0]
                llData = loop[1]
                lstStrCif += [f" {sKey.decode() if isinstance(sKey, bytes) else str(sKey)}" for sKey in lKeys]
                for lData in llData:
                    sLine = " "
                    for key in lKeys:
                        sRawValue = lData[key]
                        if isinstance(sRawValue, bytes):
                            sRawValue = sRawValue.decode()
                        else:
                            sRawValue = str(sRawValue)
                        if sRawValue.find("\n") > -1:  # should add value  between ;;
                            lstStrCif += [sLine, ";", str(sRawValue), ";"]
                            sLine = " "
                        else:
                            if len(sRawValue.split()) > 1:  # should add value between ''
                                value = "'%s'" % (sRawValue)
                            else:
                                value = str(sRawValue)
                            if len(sLine) + len(value) > 78:
                                lstStrCif += [sLine]
                                sLine = " " + value
                            else:
                                sLine += " " + value
                    lstStrCif.append(sLine)
                lstStrCif.append("")
        return linesep.join(lstStrCif)

    def exists(self, sKey):
        """
        Check if the key exists in the CIF and is non empty.

        :param str sKey: CIF key
        :param cif: CIF dictionary
        :return: True if the key exists in the CIF dictionary and is non empty
        :rtype: boolean
        """
        bExists = False
        if sKey in self:
            if len(self[sKey]) >= 1:
                if self[sKey][0] not in (self.QUESTIONMARK, self.DOT):
                    bExists = True
        return bExists

    def existsInLoop(self, sKey):
        """
        Check if the key exists in the CIF dictionary.

        :param str sKey: CIF key
        :param cif: CIF dictionary
        :return: True if the key exists in the CIF dictionary and is non empty
        :rtype: boolean
        """
        if not self.exists(self.LOOP):
            return False
        bExists = False
        if not bExists:
            for i in self[self.LOOP]:
                for j in i[0]:
                    if j == sKey:
                        bExists = True
        return bExists

    def loadCHIPLOT(self, _strFilename):
        """
        Load the powder diffraction CHIPLOT file and returns the
        pd_CIF dictionary in the object

        :param str _strFilename: the name of the file to open
        :return: the CIF object corresponding to the powder diffraction
        :rtype: dictionary
        """
        if not os.path.isfile(_strFilename):
            errStr = "I cannot find the file %s" % _strFilename
            logger.error(errStr)
            raise IOError(errStr)
        lInFile = open(_strFilename, "r").readlines()
        self["_audit_creation_method"] = 'From 2-D detector using FIT2D and CIFfile'
        self["_pd_meas_scan_method"] = "fixed"
        self["_pd_spec_description"] = lInFile[0].strip()
        try:
            iLenData = int(lInFile[3])
        except ValueError:
            iLenData = None
        lOneLoop = []
        try:
            f2ThetaMin = float(lInFile[4].split()[0])
            last = ""
            for sLine in lInFile[-20:]:
                if sLine.strip() != "":
                    last = sLine.strip()
            f2ThetaMax = float(last.split()[0])
            limitsOK = True

        except (ValueError, IndexError):
            limitsOK = False
            f2ThetaMin = 180.0
            f2ThetaMax = 0
#        print "limitsOK:", limitsOK
        for sLine in lInFile[4:]:
            sCleaned = sLine.split("#")[0].strip()
            data = sCleaned.split()
            if len(data) == 2:
                if not limitsOK:
                    f2Theta = float(data[0])
                    if f2Theta < f2ThetaMin:
                        f2ThetaMin = f2Theta
                    if f2Theta > f2ThetaMax:
                        f2ThetaMax = f2Theta
                lOneLoop.append({"_pd_meas_intensity_total": data[1]})
        if not iLenData:
            iLenData = len(lOneLoop)
        assert (iLenData == len(lOneLoop))
        self["_pd_meas_2theta_range_inc"] = "%.4f" % ((f2ThetaMax - f2ThetaMin) / (iLenData - 1))
        if self["_pd_meas_2theta_range_inc"] < 0:
            self["_pd_meas_2theta_range_inc"] = abs(self["_pd_meas_2theta_range_inc"])
            tmp = f2ThetaMax
            f2ThetaMax = f2ThetaMin
            f2ThetaMin = tmp
        self["_pd_meas_2theta_range_max"] = "%.4f" % f2ThetaMax
        self["_pd_meas_2theta_range_min"] = "%.4f" % f2ThetaMin
        self["_pd_meas_number_of_points"] = str(iLenData)
        self[self.LOOP] = [[["_pd_meas_intensity_total"], lOneLoop]]

    @staticmethod
    def LoopHasKey(loop, key):
        "Returns True if the key (string) exist in the array called loop"""
        try:
            loop.index(key)
            return True
        except ValueError:
            return False


cbfimage = CbfImage


class PilatusKey(NamedTuple):
    keyword: str
    key_index: int = 0
    value_indices: list = [1]
    types: list = [str]
    repr: str = "{}"


class PilatusHeader(object):
    KEYWORDS = OrderedDict()
    KEYWORDS["Detector"] = PilatusKey("Detector", 0, slice(1, None), str, "Detector: {}")
    KEYWORDS["sensor"] = PilatusKey("sensor", 1, [0, 3], [str, float], "{} sensor, thickness {} m")
    KEYWORDS["Pixel_size"] = PilatusKey("Pixel_size", 0, [1, 4], [float, float], "Pixel_size {} m x {} m")
    KEYWORDS["Exposure_time"] = PilatusKey("Exposure_time", 0, [1], [float], "Exposure_time {} s")
    KEYWORDS["Exposure_period"] = PilatusKey("Exposure_period", 0, [1], [float], "Exposure_period {} s")
    KEYWORDS["Tau"] = PilatusKey("Tau", 0, [1], [float], "Tau = {} s")
    KEYWORDS["Count_cutoff"] = PilatusKey("Count_cutoff", 0, [1], [int], "Count_cutoff {} counts")
    KEYWORDS["Threshold_setting"] = PilatusKey("Threshold_setting", 0, [1], [float], "Threshold_setting: {} eV")
    KEYWORDS["Gain_setting"] = PilatusKey("Gain_setting", 0, [1, 2], [str, str], "Gain_setting: {} {} (vrf = -0.200)")
    KEYWORDS["N_excluded_pixels"] = PilatusKey("N_excluded_pixels", 0, [1], [int], "N_excluded_pixels = {}")
    KEYWORDS["Excluded_pixels"] = PilatusKey("Excluded_pixels", 0, [1], [str], "Excluded_pixels: {}")
    KEYWORDS["Flat_field"] = PilatusKey("Flat_field", 0, [1], [str], "Flat_field: {}")
    KEYWORDS["Trim_file"] = PilatusKey("Trim_file", 0, [1], [str], "Trim_file: {}")
    KEYWORDS["Image_path"] = PilatusKey("Image_path", 0, [1], [str], "Image_path: {}")
    KEYWORDS["Wavelength"] = PilatusKey("Wavelength", 0, [1], [float], "Wavelength {} A")
    KEYWORDS["Energy_range"] = PilatusKey("Energy_range", 0, [1, 2], [float, float], "Energy_range {} {} eV")
    KEYWORDS["Detector_distance"] = PilatusKey("Detector_distance", 0, [1], [float], "Detector_distance {} m")
    KEYWORDS["Detector_Voffset"] = PilatusKey("Detector_Voffset", 0, [1], [float], "Detector_Voffset {} m")
    KEYWORDS["Beam_xy"] = PilatusKey("Beam_xy", 0, [1, 2], [float, float], "Beam_xy ({}, {}) pixels")
    KEYWORDS["Flux"] = PilatusKey("Flux", 0, [1], [float], "Flux {}")
    KEYWORDS["Filter_transmission"] = PilatusKey("Filter_transmission", 0, [1], [float], "Filter_transmission {}")
    KEYWORDS["Start_angle"] = PilatusKey("Start_angle", 0, [1], [float], "Start_angle {} deg.")
    KEYWORDS["Angle_increment"] = PilatusKey("Angle_increment", 0, [1], [float], "Angle_increment {} deg.")
    KEYWORDS["Detector_2theta"] = PilatusKey("Detector_2theta", 0, [1], [float], "Detector_2theta {} deg.")
    KEYWORDS["Polarization"] = PilatusKey("Polarization", 0, [1], [float], "Polarization {}")
    KEYWORDS["Alpha"] = PilatusKey("Alpha", 0, [1], [float], "Alpha {} deg.")
    KEYWORDS["Kappa"] = PilatusKey("Kappa", 0, [1], [float], "Kappa {} deg.")
    KEYWORDS["Phi"] = PilatusKey("Phi", 0, [1], [float], "Phi {} deg.")
    KEYWORDS["Phi_increment"] = PilatusKey("Phi_increment", 0, [1], [float], "Phi_increment {} deg.")
    KEYWORDS["Chi"] = PilatusKey("Chi", 0, [1], [float], "Chi {} deg.")
    KEYWORDS["Chi_increment"] = PilatusKey("Chi_increment", 0, [1], [float], "Chi_increment {} deg.")
    KEYWORDS["Omega"] = PilatusKey("Omega", 0, [1], [float], "Omega {} deg.")
    KEYWORDS["Omega_increment"] = PilatusKey("Omega_increment", 0, [1], [float], "Omega_increment {} deg.")
    KEYWORDS["Oscillation_axis"] = PilatusKey("Oscillation_axis", 0, [1], [str], "Oscillation_axis {}")
    KEYWORDS["N_oscillations"] = PilatusKey(" ('N_oscillations", 0, [1], [int], "N_oscillations {}")
    KEYWORDS["Start_position"] = PilatusKey("Start_position", 0, [1], [float], "Start_position {}")
    KEYWORDS["Position_increment"] = PilatusKey("Position_increment", 0, [1], [float], "Position_increment")
    KEYWORDS["Shutter_time"] = PilatusKey("Shutter_time", 0, [1], [float], "Shutter_time {} s")
    SPACE_LIKE = "()#:=,"

    @classmethod
    def clean_string(cls, input_string):
        tmp = str(input_string)
        for k in cls.SPACE_LIKE:
            tmp = tmp.replace(k, " ")
        return tmp

    def __init__(self, content, convention="PILATUS_1.2"):
        assert convention == "PILATUS_1.2"
        self._dict = self._parse(content)

    def __repr__(self):
        lines = []
        for key, descr in self.KEYWORDS.items():
            value = self._dict.get(key)
            if value is None:
                continue
            if isinstance(value, (list, tuple)):
                line = descr.repr.format(*value)
            else:
                line = descr.repr.format(value)
            lines.append("# " + line)
        return "\n".join(lines)

    def _parse(self, content):
        lines = self.clean_string(content).split("\n")
        dico = OrderedDict()
        for line in lines:
            words = line.split()
            if not words:
                continue
            for k, v in self.KEYWORDS.items():
                if words[v.key_index] == k:
                    if isinstance(v.types, (list, tuple)):
                        if len(v.value_indices) == 1:
                            dico[k] = v.types[0]((words[v.value_indices[0]]))
                        else:
                            dico[k] = tuple(i(words[j]) for i, j in zip(v.types, v.value_indices))
                    else:
                        if isinstance(v.value_indices, slice):
                            dico[k] = " ".join([v.types(i) for i in words[v.value_indices]])
                        else:
                            dico[k] = v.types(words[v.value_indices])
        return dico

    def __setitem__(self, key, value):
        if key not in self.KEYWORDS:
            logger.warning("Unknown key: %s", key)
        self._dict[key] = value

    def __getitem__(self, key):
        return self._dict[key]
