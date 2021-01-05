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
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""

Authors: Henning O. Sorensen & Erik Knudsen
         Center for Fundamental Research: Metal Structures in Four Dimensions
         Risoe National Laboratory
         Frederiksborgvej 399
         DK-4000 Roskilde
         email:erik.knudsen@risoe.dk

+ mods for fabio by JPW

"""

import numpy
import re

import logging

from .fabioimage import FabioImage

logger = logging.getLogger(__name__)

_DATA_TYPES = {
    "signed char": numpy.int8,
    "unsigned char": numpy.uint8,
    "short int": numpy.int16,
    "unsigned short int": numpy.uint16,
    "long int": numpy.int32,
    "unsigned long int": numpy.uint32,
    "float IEEE": numpy.float32,
    # Valid but unsupported
    "Compressed": None,
    # Valid but unsupported
    "Other_type": None,
}
"""Mapping from Data_type content to numpy equicalent"""


class DtrekImage(FabioImage):
    """Read an image using the d*TREK format.

    This format is used to process X-ray diffraction data from area detectors.
    It supports processing of data from multiple detector types (imaging plates,
    CCDs and pixel arrays) and from multiple vendors (Rigaku, Mar, Dectris,
    Bruker and ADSC).

    Rigaku providing a `specification <https://www.rigaku.com/downloads/software/free/dTREK%20Image%20Format%20v1.1.pdf>`_.
    """

    DESCRIPTION = "D*trek format (Rigaku specification 1.1)"

    DEFAULT_EXTENSIONS = ["img"]

    _keyvalue_pattern = None

    def __init__(self, *args, **kwargs):
        FabioImage.__init__(self, *args, **kwargs)
        if DtrekImage._keyvalue_pattern is None:
            DtrekImage._keyvalue_pattern = re.compile(b"[^\n]+")

    def read(self, fname, frame=None):
        """ read in the file """
        with self._open(fname, "rb") as infile:
            try:
                self._readheader(infile)
            except Exception:
                logger.debug("Backtrace", exc_info=True)
                raise IOError("Error processing d*TREK header")

            # FIXME: It would be good to read only the expected data
            binary = infile.read()

        # Read information of the binary data type
        data_type = self.header.get("Data_type", None)
        if data_type is None:
            # Compatibility with old supported files
            data_type = self.header.get("TYPE", None)
            if data_type is not None and data_type == "unsigned_short":
                pass
            else:
                logger.warning("Data_type key is mandatory. Fallback to unsigner integer 16-bits.")
            numpy_type = numpy.uint16
        else:
            if data_type not in _DATA_TYPES:
                raise IOError("Data_type key contains an invalid/unsupported value: %s", data_type)
            numpy_type = _DATA_TYPES[data_type]
            if type is None:
                raise IOError("Data_type %s is not supported by fabio", data_type)

        # Stored in case data reading fails
        self._dtype = numpy.dtype(numpy_type)

        dim = self.header.get("DIM", None)
        if dim is None:
            logger.warning("DIM key is mandatory. Fallback using DIM=2.")
            dim = 2
        else:
            dim = int(dim)

        shape = []
        for i in range(dim):
            value = int(self.header['SIZE%d' % (i + 1)])
            shape.insert(0, value)
        self._shape = shape

        if sum(shape) == 0:
            data = None
        else:
            # Read the data into the array
            data = numpy.frombuffer(binary, numpy_type).copy()
            if self.swap_needed():
                try:
                    data.byteswap(inplace=True)
                except TypeError:
                    # Older numpy without inplace
                    data = data.byteswap()
            try:
                data.shape = self._shape
            except ValueError:
                    raise IOError('Size spec in d*TREK header does not match ' +
                                  'size of image data field %s != %s' % (self._shape, data.size))
        self.data = data
        self._shape = None
        self._dtype = None
        self.resetvals()
        return self

    def _split_meta(self, line):
        """Split a line into key and value.

        :param bytes line: A line of bytes
        :rtype: Tuple[str,str]
        """
        if b"=" not in line:
            raise ValueError("No meta")
        line = line.decode("ascii")
        key, value = line.split('=')
        return key.strip(), value.strip(' ;\n\r')

    def _readheader(self, infile):
        """Read a d*TREK header.

        After the execusion of this function, the cursor on infile will point
        at the end of the header (at the start of the binary data block).

        :param FileObject infile: A file object pointing at the first character
            of the header.
        """
        header_line = infile.readline()
        assert(header_line.startswith(b"{"))
        header_bytes_line = infile.readline()
        key, header_bytes = self._split_meta(header_bytes_line)
        assert(key == "HEADER_BYTES")
        self.header[key] = header_bytes
        header_bytes = int(header_bytes)

        # Read the remining block
        # For robustness, cause that's in fact a const
        header_bytes -= len(header_line) + len(header_bytes_line)
        header_block = infile.read(header_bytes)

        for line in DtrekImage._keyvalue_pattern.finditer(header_block):
            line = line.group(0)
            if line.startswith(b'}'):
                # Remining part is padding
                return
            try:
                key, value = self._split_meta(line)
                self.header[key] = value
            except ValueError:
                pass

        # It means there was no end of block
        logger.warning("The end of block '}' was not reachable. File may be corrupted.")

    def write(self, fname):
        """
        Write d*TREK format
        """

        # From specification
        HEADER_START = b"{\n"
        HEADER_END = b"}\n\x0C\n"
        HEADER_BYTES_TEMPLATE = "HEADER_BYTES=% 5d;\n"
        # start + end + header_bytes_key + header_bytes_value + header_bytes_end
        MINIMAL_HEADER_SIZE = 2 + 4 + 13 + 5 + 2

        data = self.data
        if data is not None:
            dtrek_data_type = None
            for key, value in _DATA_TYPES.items():
                if data.dtype.type == value:
                    dtrek_data_type = key
                    break

            if dtrek_data_type is None:
                if data.dtype.kind == 'f':
                    dtrek_data_type = "float IEEE"
                elif data.dtype.kind == 'u':
                    dtrek_data_type = "unsigned long int"
                elif data.dtype.kind == 'i':
                    dtrek_data_type = "long int"
                else:
                    raise TypeError("Unsupported data type %s", data.dtype)
                new_dtype = numpy.dtype(_DATA_TYPES[dtrek_data_type])
                logger.warning("Data type %s unsupported. Store it as %s.", data.dtype, new_dtype)
                data = data.astype(new_dtype)

            byte_order = self._get_dtrek_byte_order(default_little_endian=numpy.little_endian)
            little_endian = byte_order == "little_endian"
            if little_endian != numpy.little_endian:
                data = data.byteswap()

            # Patch header to match the data
            self.header["Data_type"] = dtrek_data_type
            self.header['DIM'] = str(len(data.shape))
            for i, size in enumerate(reversed(data.shape)):
                self.header['SIZE%d' % (i + 1)] = str(size)
            self.header["BYTE_ORDER"] = byte_order
        else:
            # No data
            self.header["Data_type"] = "long int"
            self.header['DIM'] = "2"
            self.header["SIZE1"] = "0"
            self.header["SIZE2"] = "0"
            self.header["BYTE_ORDER"] = "little_endian"

        out = b""
        for key in self.header:
            if key == "HEADER_BYTES":
                continue
            line = "%s= %s;\n" % (key, self.header[key])
            out += line.encode("utf-8")

        # FIXME: This code do not take into account the size of "HEADER_BYTES"
        if "HEADER_BYTES" in self.header:
            hsize = int(self.header["HEADER_BYTES"])
            pad = hsize - len(out) - MINIMAL_HEADER_SIZE
            if pad < 0:
                logger.warning("HEADER_BYTES have to be patched.")
                minimal_hsize = hsize - pad
                hsize = (minimal_hsize + 512) & ~(512 - 1)
                pad = hsize - minimal_hsize
        else:
            minimal_hsize = len(out) + MINIMAL_HEADER_SIZE
            hsize = (minimal_hsize + 512) & ~(512 - 1)
            pad = hsize - minimal_hsize

        header_bytes = HEADER_BYTES_TEMPLATE % hsize
        out = HEADER_START + header_bytes.encode("ascii") + out + HEADER_END + (b' ' * pad)
        assert len(out) % 512 == 0, "Header is not multiple of 512"

        with open(fname, "wb") as outf:
            outf.write(out)
            if data is not None:
                data.tofile(outf)

    def _get_dtrek_byte_order(self, default_little_endian=None):
        """Returns the byte order value in d*TREK format."""
        if "BYTE_ORDER" not in self.header:
            if default_little_endian is None:
                logger.warning("No byte order specified, assuming little_endian")
                little_endian = True
            else:
                little_endian = default_little_endian
        else:
            byte_order = self.header["BYTE_ORDER"]
            little_endian = "little" in byte_order
            big_endian = "big" in byte_order
            if not little_endian and not big_endian:
                logger.warning("Invalid BYTE_ORDER value. Found '%s', assuming little_endian", byte_order)
                little_endian = True

        if little_endian:
            return "little_endian"
        else:
            return "big_endian"

        return byte_order

    def swap_needed(self, check=True):
        """
        Returns True if the header does not use the same endianness than the
        system.

        :rtype: bool
        """
        byte_order = self._get_dtrek_byte_order()
        little_endian = byte_order == "little_endian"
        return little_endian != numpy.little_endian
