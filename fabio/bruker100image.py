# coding: utf-8
#
#    Project: X-ray image reader
#             https://github.com/kif/fabio
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


         Jérôme Kieffer, ESRF, Grenoble, France
         Sigmund Neher, GWDG, Göttingen, Germany

"""
# get ready for python3
from __future__ import absolute_import, print_function, with_statement, division
__authors__ = ["Henning O. Sorensen" , "Erik Knudsen", "Jon Wright",
               "Jérôme Kieffer", "Sigmund Neher" ]
__date__ = "24/05/2016"
__status__ = "production"
__copyright__ = "2007-2009 Risoe National Laboratory; 2015-2016 ESRF, 2016 GWDG"
__licence__ = "GPLv3+"

import numpy
import logging
import os
from math import ceil
logger = logging.getLogger("bruker100image")
try:
    from PIL import Image
except ImportError:
    logger.warning("PIL is not installed ... trying to do without")
    Image = None

from .brukerimage import BrukerImage
from .readbytestream import readbytestream
from .fabioutils import pad, StringTypes


class Bruker100Image(BrukerImage):

    bpp_to_numpy = {1: numpy.uint8,
                    2: numpy.uint16,
                    4: numpy.uint32}

    def __init__(self, data=None, header=None):
        BrukerImage.__init__(self, data, header)
        self.version = 100

    def toPIL16(self, filename=None):
        if not Image:
            raise RuntimeError("PIL is not installed !!! ")

        if filename:
            self.read(filename)
        PILimage = Image.frombuffer("F",
                                        (self.dim1, self.dim2),
                                        self.data,
                                        "raw",
                                        "F;16", 0, -1)
        return PILimage

    def read(self, fname, frame=None):
        '''data is stored in three blocks: data (uint8), overflow (uint32), underflow (int32). The blocks are
        zero paded to a multiple of 16 bits  '''
        with self._open(fname, "rb") as infile:
            try:
                self._readheader(infile)
            except:
                raise
            rows = self.dim1
            cols = self.dim2
            npixelb = int(self.header['NPIXELB'][0])
            # you had to read the Bruker docs to know this!

            # We are now at the start of the image - assuming bruker._readheader worked
            # Get image block size from NPIXELB.
            # The total size is nbytes * nrows * ncolumns.
            self.data = readbytestream(infile, infile.tell(), rows, cols, npixelb,
                                       datatype="int", signed='n', swap='n')
            # now process the overflows
            for k, nover in enumerate(self.header['NOVERFL'].split()):
                if k == 0:
                    # read the set of "underflow pixels" - these will be completely disregarded for now
                    continue
                nov = int(nover)
                if nov <= 0:
                    continue
                bpp = 1 << k  # (2 ** k)
                datatype = self.bpp_to_numpy[bpp]
                # upgrade data type
                self.data = self.data.astype(datatype)
                # pad nov*bpp to a multiple of 16 bytes
                nbytes = (nov * bpp + 15) & ~(15)
                # Multiple of 16 just above
                data_str = infile.read(nbytes)
                # ar without zeros
                ar = numpy.fromstring(data_str[:nov * bpp], datatype)
                # insert the the overflow pixels in the image array:
                lim = (1 << (8 * k)) - 1

                # generate an array comprising of the indices into data.ravel()
                # where its value equals lim.
                flat = self.data.ravel()
                mask = numpy.where(flat == lim)[0]
                # now put values from ar into those indices
                flat.put(mask, ar)
                logger.debug("%s bytes read + %d bytes padding" % (nov * bpp, nbytes - nov * bpp))
#         infile.close()

        self.resetvals()
        return self

    def gen_header100(self):
        """
        Generate headers (with some magic and guesses)
        @param format can be 86 or 100
        """
        headers = []
        for key in self.HEADERS_KEYS:
            if key in self.header:
                value = self.header[key]
                if key == "CFR":
                    line = key.ljust(1) + ":"
                else:
                    line = key.ljust(7) + ":"
                if type(value) in StringTypes:
                    if key == 'NOVERFL':
                        line += str(-1).ljust(24) + str(self.noverf).ljust(24) + str(self.nunderf)
                    elif key == "DETTYPE":
                        line += str(value)
                    elif key == "CFR":
                        line += str(value)
                    elif os.linesep in value:
                        lines = value.split(os.linesep)
                        for i in lines[:-1] :
                            headers.append((line + str(i)).ljust(80, " "))
                            line = key.ljust(7) + ":"
                        line += str(lines[-1])
                    elif len(value) < 72:
                        line += str(value)
                    else:
                        for i in range(len(value) // 72):
                            headers.append((line + str(value[72 * i:72 * (i + 1)])))
                            line = key.ljust(7) + ":"
                        line += value[72 * (i + 1):]
                elif "__len__" in dir(value):
                    f = "\%.%is" % 72 // len(value) - 1
                    line += " ".join([f % i for i in value])
                else:
                    line += str(value)
                headers.append(line.ljust(80, " "))
        header = "".join(headers)
        if len(header) > 512 * self.header["HDRBLKS"]:
            tmp = ceil(len(header) / 512.0)
            self.header["HDRBLKS"] = 15  # int(ceil(tmp / 5.0) * 5.0)
            for i in range(len(headers)):
                if headers[i].startswith("HDRBLKS"):
                    headers[i] = ("HDRBLKS:%s" % self.header["HDRBLKS"]).ljust(80, " ")
        res = pad("".join(headers), self.SPACER + "."*78, 512 * int(self.header["HDRBLKS"]))
        return res

    def gen_overflow100(self):
        """
        Generate an overflow table, including the underflow, marked as 65535 . 
        """
        bpp = 2
        limit = 255
        # noverf = int(self.header['NOVERFL'].split()[1])
        noverf = self.noverf
        read_bytes = (noverf * bpp + 15) & ~(15)  # since data b
        dif2usedbyts = read_bytes - (noverf * bpp)
        pad_zeros = numpy.zeros(dif2usedbyts / bpp).astype(self.bpp_to_numpy[bpp])
        flat = self.data.ravel()  # flat memory view
        flow_pos = numpy.logical_or(flat >= limit, flat < 0)
#         flow_pos_indexes = numpy.where(flow_pos)[0]
        flow_vals = (flat[flow_pos])

        flow_vals[flow_vals < 0] = 65535  # limit#flow_vals[flow_vals<0]
        flow_vals_paded = numpy.hstack((flow_vals, pad_zeros)).astype(self.bpp_to_numpy[bpp])
        return flow_vals_paded  # pad(overflow, ".", 512)

    def gen_underflow100(self):
        """
        Generate an underflow table
        """
        bpp = 4
        noverf = int(self.header['NOVERFL'].split()[2])
        nunderf = self.nunderf
        read_bytes = (noverf * bpp + 15) & ~(15)
        dif2usedbyts = read_bytes - (noverf * bpp)
        pad_zeros = numpy.zeros(dif2usedbyts / bpp).astype(self.bpp_to_numpy[bpp])
        flat = self.data.ravel()  # flat memory view
        underflow_pos = numpy.where(flat < 0)[0]
        underflow_val = flat[underflow_pos]
        underflow_val = underflow_val.astype(self.bpp_to_numpy[bpp])
        nderflow_val_paded = numpy.hstack((underflow_val, pad_zeros))
        return nderflow_val_paded

    def write(self, fname):
        """
        Write a bruker image

        """
        if numpy.issubdtype(self.data.dtype, float):
            if "LINEAR" in self.header:
                try:
                    slope, offset = self.header["LINEAR"].split(None, 1)
                    slope = float(slope)
                    offset = float(offset)
                except Exception:
                    logger.warning("Error in converting to float data with linear parameter: %s" % self.header["LINEAR"])
                    slope, offset = 1.0, 0.0

            else:
                offset = self.data.min()
                max_data = self.data.max()
                max_range = 2 ** 24 - 1  # similar to the mantissa of a float32
                if max_data > offset:
                    slope = (max_data - offset) / float(max_range)
                else:
                    slope = 1.0
            tmp_data = numpy.round(((self.data - offset) / slope)).astype(numpy.uint32)
            self.header["LINEAR"] = "%s %s" % (slope, offset)

        else:
            tmp_data = self.data
        minusMask = numpy.where(tmp_data < 0)
        bpp = self.calc_bpp(tmp_data)
        # self.basic_translate(fname)
        limit = 2 ** (8 * bpp) - 1
        data = tmp_data.astype(self.bpp_to_numpy[bpp])
        reset = numpy.where(tmp_data >= limit)
        self.noverf = len(reset[0]) + len(minusMask[0])
        self.nunderf = len(minusMask[0])
        data[reset] = limit
        data[minusMask] = limit
        if not numpy.little_endian and bpp > 1:
            # Bruker enforces little endian
            data.byteswap(True)
        with self._open(fname, "wb") as bruker:
            bruker.write(self.gen_header100().encode("ASCII"))
            bruker.write(data.tostring())
            bruker.write(self.gen_overflow100())
            bruker.write(self.gen_underflow100())


bruker100image = Bruker100Image
