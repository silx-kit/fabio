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
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#  OTHER DEALINGS IN THE SOFTWARE.

"""Authors: Henning O. Sorensen & Erik Knudsen
         Center for Fundamental Research: Metal Structures in Four Dimensions
         Risoe National Laboratory
         Frederiksborgvej 399
         DK-4000 Roskilde
         email:erik.knudsen@risoe.dk


         Jérôme Kieffer, ESRF, Grenoble, France
         Sigmund Neher, GWDG, Göttingen, Germany

"""

__authors__ = ["Henning O. Sorensen", "Erik Knudsen", "Jon Wright",
               "Jérôme Kieffer", "Sigmund Neher"]
__status__ = "production"
__copyright__ = "2007-2009 Risoe National Laboratory; 2015-2020 ESRF, 2016 GWDG"
__licence__ = "MIT"

import io
import os
from math import ceil
import logging
import numpy

logger = logging.getLogger(__name__)

from .brukerimage import BrukerImage
from .readbytestream import readbytestream
from .fabioutils import pad, StringTypes


class Bruker100Image(BrukerImage):

    DESCRIPTION = "SFRM File format used by Bruker detectors (version 100)"

    DEFAULT_EXTENSIONS = ["sfrm"]

    bpp_to_numpy = {1: numpy.uint8,
                    2: numpy.uint16,
                    4: numpy.int32}
    version = 100

    def __init__(self, data=None, header=None):
        BrukerImage.__init__(self, data, header)
        self.nunder = self.nover1 = self.nover2 = 0
        self.baseline = None
        self.ar_underflows = None
        if data is not None:
            self.init_overflow(data)

    def _readheader(self, infile):
        """
        The bruker format uses 80 char lines in key : value format
        In the first 512*5 bytes of the header there should be a
        HDRBLKS key, whose value denotes how many 512 byte blocks
        are in the total header. The header is always n*5*512 bytes,
        otherwise it wont contain whole key: value pairs
        """
        line = 80
        blocksize = 512
        nhdrblks = 5  # by default we always read 5 blocks of 512
        self.__headerstring = infile.read(blocksize * nhdrblks).decode("ASCII")
        self.header = self.check_header()
        for i in range(0, nhdrblks * blocksize, line):
            if self.__headerstring[i: i + line].find(":") > 0:
                key, val = self.__headerstring[i: i + line].split(":", 1)
                key = key.strip()  # remove the whitespace (why?)
                val = val.strip()
                if key in self.header:
                    # append lines if key already there
                    self.header[key] = self.header[key] + os.linesep + val
                else:
                    self.header[key] = val
        # we must have read this in the first 5*512 bytes.
        nhdrblks = int(self.header['HDRBLKS'])
        self.header['HDRBLKS'] = nhdrblks
        # Now read in the rest of the header blocks, appending
        self.__headerstring += infile.read(blocksize * (nhdrblks - 5)).decode("ASCII")
        for i in range(5 * blocksize, nhdrblks * blocksize, line):
            if self.__headerstring[i: i + line].find(":") > 0:  # as for first 512 bytes of header
                key, val = self.__headerstring[i: i + line].split(":", 1)
                key = key.strip()
                val = val.strip()
                if key in self.header:
                    self.header[key] = self.header[key] + os.linesep + val
                else:
                    self.header[key] = val
        # set the image dimensions
        shape = int(self.header['NROWS'].split()[0]), int(self.header['NCOLS'].split()[0])
        self._shape = shape
        self.version = int(self.header.get('VERSION', "100"))

    def read(self, fname, frame=None):
        """Read the data.

        Data is stored in three blocks:

        - data (uint8)
        - overflow (uint32)
        - underflow (int32).

        The blocks are zero padded to a multiple of 16 bytes.
        """
        with self._open(fname, "rb") as infile:
            self._readheader(infile)
            rows, cols = self.shape
            bpp = int(self.header['NPIXELB'][0])
            # you had to read the Bruker docs to know this!

            # We are now at the start of the image - assuming bruker._readheader worked
            # Get image block size from NPIXELB.
            # The total size is nbytes * nrows * ncolumns.

            print("Before read, we are at", infile.tell())

            datablock_size = rows * cols * bpp
            datablock_size_padded = int(ceil(datablock_size / 512) * 512)
            datablock = infile.read(datablock_size_padded)
            data = numpy.frombuffer(datablock[:datablock_size], dtype=numpy.dtype(f"uint{8*bpp}")).reshape(self.shape)
#             self.data = readbytestream(infile, infile.tell(), rows, cols, bpp,
#                                        datatype="int", signed='n', swap='n').astype(numpy.int32)

            # now process the overflows
            noverfl_values = [int(f) for f in self.header['NOVERFL'].split()]
            array_underflows = None
            for k, nov in enumerate(noverfl_values):
                # may be underflow, overflow 16 bits and overflow 32 bits.
                if k>=3:
                    break
                if nov <= 0:
                    continue

                if k == 0: #Underflow: values are negative!
                    bpp = int(self.header['NPIXELB'].split()[1])
                    datatype = numpy.dtype(f"int{bpp*8}")
                else:
                    bpp = 2 * k  # now wise, 1-> 16 bits; 2 -> 32 bits
                    datatype = numpy.dtype(f"uint{bpp*8}")
                # pad nov*bpp to a multiple of 16 bytes
                nbytes = int(ceil((nov * bpp) / 16) * 16)

                # Multiple of 16 just above
                data_str = infile.read(nbytes)
                # ar without zeros
                print(f"in read {k}, bpp {bpp}, nov {nov} nbytes {nbytes} datatype {datatype}")
                ar = numpy.frombuffer(data_str[:nov * bpp], datatype)

                logger.debug("%s bytes read + %d bytes padding" % (nov * bpp, nbytes - nov * bpp))

                if k == 0:
                    # read the set of "underflow pixels" - these will be completely disregarded for now
                    array_underflows = ar
                    continue

                # insert the the overflow pixels in the image array:
                lim = numpy.iinfo(datatype).max

                # upgrade data type
                data = data.astype(datatype)

                # generate an array comprising of the indices into data.ravel()
                # where its value equals lim.
                flat = data.ravel()
                mask = numpy.where(flat == lim)[0]
                # now put values from ar into those indices
                flat.put(mask, ar)

        # replace zeros with values from underflow block
        if (noverfl_values[0] > 0) and (array_underflows is not None):
            new_dtype = numpy.dtype(f"int{data.dtype.itemsize * 2 * 8}") # switch to signed integrer when underflow 
            data = data.astype(new_dtype)
            flat = data.ravel()
            mask_undeflows = numpy.where(flat == 0)[0]
            mask_no_undeflows = numpy.where(self.data >= 0)
            flat.put(mask_undeflows, ar_underflows)

        # add baseline
        if noverfl_values[0] != -1:
            baseline = int(self.header["NEXP"].split()[2])
            data[self.mask_no_undeflows] += baseline

        self.resetvals()
        return self

    def gen_header(self):
        """
        Generate headers (with some magic and guesses)
        format is Bruker100
        """
        headers = []
        for key in self.HEADERS_KEYS:
            if key in self.header:
                value = self.header[key]
                if key == "CFR":
                    line = key.ljust(4) + ":"
                else:
                    line = key.ljust(7) + ":"
                if type(value) in StringTypes:
                    if key == 'NOVERFL':
                        line += str(str(self.nunder).ljust(24, ' ') + str(self.nover1).ljust(24) + str(self.nover2))
                    elif key == "DETTYPE":
                        line += str(value)
                    elif key == "CFR":
                        line += str(value)
                    elif os.linesep in value:
                        lines = value.split(os.linesep)
                        for i in lines[:-1]:
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
                    f = "%%.%is" % (72 // len(value) - 1)
                    line += " ".join([f % i for i in value])
                else:
                    line += str(value)
                headers.append(line.ljust(80, " "))
        header_size = sum(len(i) for i in headers)
        if  header_size > 512 * self.header["HDRBLKS"]:
            hdr_blocks = ceil(header_size / 512.0)
            self.header["HDRBLKS"] = int(ceil(hdr_blocks / 5.0) * 5.0)
            print(self.header["HDRBLKS"], header_size)
            for i in range(len(headers)):
                if headers[i].startswith("HDRBLKS"):
                    headers[i] = ("HDRBLKS:%s" % self.header["HDRBLKS"]).ljust(80, " ")
        res = pad("".join(headers), self.SPACER + "." * 78, 512 * int(self.header["HDRBLKS"]))
        return res

    def gen_overflow(self):
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
        # flow_pos_indexes = numpy.where(flow_pos)[0]
        flow_vals = (flat[flow_pos])

        flow_vals[flow_vals < 0] = 65535  # limit#flow_vals[flow_vals<0]
        flow_vals_paded = numpy.hstack((flow_vals, pad_zeros)).astype(self.bpp_to_numpy[bpp])
        return flow_vals_paded  # pad(overflow, ".", 512)

    def write(self, fname):
        """Write a bruker image

        """
        if "NOVERFL" not in self.header:
            self.init_overflow(self.data)

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
            tmp_data = self.data.copy()
            if int(self.header["NOVERFL"].split()[0]) > 0:
                baseline = int(self.header["NEXP"].split()[2])
                tmp_data[self.mask_no_undeflows] -= baseline

        minusMask = numpy.where(tmp_data < 0)
        bpp = self.calc_bpp(tmp_data)
        # self.basic_translate(fname)
        limit = 2 ** (8 * bpp) - 1
        data = tmp_data.astype(self.bpp_to_numpy[bpp])
        reset = numpy.where(tmp_data >= limit)
        self.nunder = int(self.header["NOVERFL"].split()[0])
        self.nover1 = len(reset[0]) + len(minusMask[0])
        self.nover2 = len(minusMask[0])
        data[reset] = limit
        data[minusMask] = limit
        if not numpy.little_endian and bpp > 1:
            # Bruker enforces little endian
            data.byteswap(True)
        with self._open(fname, "wb") as bruker:
            fast = isinstance(bruker, io.BufferedWriter)
            bruker.write(self.gen_header().encode("ASCII"))
            if fast:
                data.tofile(bruker)
            else:
                bruker.write(data.tobytes())
            overflows_one_byte = self.overflows_one_byte()
            overflows_two_byte = self.overflows_two_byte()
            if int(self.header["NOVERFL"].split()[0]) > 0:
                underflows = self.underflows()
                if fast:
                    underflows.tofile(bruker)
                else:
                    bruker.write(underflows.tobytes())
            if fast:
                overflows_one_byte.tofile(bruker)
                overflows_two_byte.tofile(bruker)
            else:
                bruker.write(overflows_one_byte.tobytes())
                bruker.write(overflows_two_byte.tobytes())

    def underflows(self):
            """
            Generate underflow table
            """
            bpp = self.ar_underflows.dtype.itemsize
            # limit = 255
            nunderFlows = self.nunder
            # temp_data = self.data
            read_bytes = int(ceil((nunderFlows * bpp) / 16) * 16)  # pad to multiple of 16
            dif2usedbyts = read_bytes - (nunderFlows * bpp)
            pad_zeros = numpy.zeros(dif2usedbyts // bpp).astype(self.ar_underflows.dtype)
            flow_vals_paded = numpy.concatenate((self.ar_underflows, pad_zeros))
            return flow_vals_paded

    def overflows_one_byte(self):
            """
            Generate one-byte overflow table
            """
            bpp = 2
            limit = 255
            nover_one = self.nover1
            # temp_data = self.data
            read_bytes = (nover_one * bpp + 15) & ~(15)  # multiple of 16
            dif2usedbyts = read_bytes - (nover_one * bpp)
            pad_zeros = numpy.zeros(dif2usedbyts // bpp, dtype=self.bpp_to_numpy[bpp])
            flat = self.data.ravel()  # flat memory view
            flow_pos = (flat >= limit) + (flat < 0)
            # flow_pos_indexes = numpy.where(flow_pos == True)[0]
            flow_vals = (flat[flow_pos])
            flow_vals[flow_vals < 0] = 65535  # limit#flow_vals[flow_vals<0]
            # print("flow_vals",flow_vals)
            flow_vals_paded = numpy.hstack((flow_vals, pad_zeros)).astype(self.bpp_to_numpy[bpp])
            return flow_vals_paded  # pad(overflow, ".", 512)

    def overflows_two_byte(self):
        """
        Generate two byte overflow table
        """

        bpp = 4
        noverf = int(self.header['NOVERFL'].split()[2])
        # nover_two = self.nover2
        read_bytes = (noverf * bpp + 15) & ~(15)  # multiple of 16
        dif2usedbyts = read_bytes - (noverf * bpp)
        pad_zeros = numpy.zeros(dif2usedbyts // bpp, dtype=self.bpp_to_numpy[bpp])
        flat = self.data.ravel()  # flat memory view

        underflow_pos = numpy.where(flat < 0)[0]
        underflow_val = flat[underflow_pos]  # [::-1]
        # underflow_val[underflow_val 0] = 65535#limit#flow_vals[flow_vals<0]

        underflow_val = underflow_val.astype(self.bpp_to_numpy[bpp])
        nderflow_val_paded = numpy.hstack((underflow_val, pad_zeros))

        return nderflow_val_paded  # pad(overflow, ".", 512)


    def init_overflow(self, data):
        """Prepare the NOVERFL value for the header when analyzing the data
        
        Nota: the values are padded to 16
        """
        if data is None:
            return

        if self.baseline is None:
            if len(self.header.get("NEXP", "").split()) >= 3:
                self.baseline = int(self.header.get("NEXP", "").split()[2])
                if self.baseline < 0:  # can be -1
                    baseline = 0
                else:
                    baseline = self.baseline
            else:
                baseline = self.baseline = 0
                self.header["NEXP"] = f"1 0 {self.baseline}"
        else:
            self.baseline = baseline = 0
            self.header["NEXP"] = f"1 0 {self.baseline}"

        data = numpy.ascontiguousarray(data, numpy.int64) - baseline
        print("Datamin", data.min(), baseline, self.baseline)
        shape = data.shape
        self.header['NROWS'] = shape[0]
        self.header['NCOLS'] = shape[1]
        flat = data.ravel()
        self.mask_undeflows = numpy.where(flat <= 0)[0]
        self.ar_underflows = flat[self.mask_undeflows]
        under = self.mask_undeflows.size
        over1 = numpy.sum(data >= 255)  # not padded
        over2 = numpy.sum(data >= 65535)  # not padded
        self.header["NOVERFL"] = f"{under} {over1} {over2}"
        self.header["HDRBLKS"] = 5  # 5*512 is a minimum size for the header. May be extended at writing
        self.mask_no_undeflows = numpy.where(self.data > 0)
        min_under = self.ar_underflows.min()
        if min_under < -32768:
            self.header["NPIXELB"] = "1 4"
            self.ar_underflows = self.ar_underflows.astype(numpy.int32)
        elif min_under < -256:
            self.header["NPIXELB"] = "1 2"
            self.ar_underflows = self.ar_underflows.astype(numpy.int16)
        else:
            self.header["NPIXELB"] = "1 1"
            self.ar_underflows = self.ar_underflows.astype(numpy.int8)
        print("NPIXELB", self.header["NPIXELB"])
            

bruker100image = Bruker100Image
