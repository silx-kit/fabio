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


def mround(value, multiple=16):
    """Round a value up to the multiple of multiple
    """
    return int(multiple * ceil(value / multiple))


def _split_data(data):
    "Split an image, return the dict with various components"
    data = data.astype("int32")  # explicit copy
    flat = data.ravel()
    mini = data.min()
    if mini >= 0:
        mode = flat.bincount().argmax()
    else:
        mean = flat.mean()
        std = flat.std()
        inliers = abs(flat - mean) / std < 3
        mode = int(flat[inliers].mean())

    if (mode - mini) < 128:
        baseline = mini - 1
    else:
        baseline = mode - 128  # Ensures the mode is in the middle of the uint8 range
    print(f"mini {mini}, mode {mode}, baseline {baseline}")
    umask = flat<=baseline
    underflow = flat[umask]
    underflow_max = max(abs(underflow.min()), abs(underflow.max()))
    underflow_dtype = numpy.dtype(f"int{mround(numpy.log2(underflow_max)+1,8)}")
    print(underflow_dtype)
    flat -= baseline
    flat[umask] = 0
    o2_mask = flat>=65535
    if numpy.any(o2_mask):
        overflow2 = flat[o2_mask]
        flat[o2_mask] = 65535
    else:
        overflow2 = None
    o1_mask = flat>=255
    if numpy.any(o1_mask):
        overflow1 = flat[o1_mask].astype(numpy.uint16)
        flat[o1_mask] = 255
    else:
        overflow1 = None
    data = flat.astype(numpy.uint8).reshape(data.shape)
    res = {"data":data, 
           "baseline": baseline,
           "underflow":underflow.astype(underflow_dtype),
           "overflow1": overflow1,
           "overflow2": overflow2
           }
    return res


def _merge_data(data, baseline=0, underflow=None, overflow1=None, overflow2=None):
    """
    Build an array from the various components
    
    :param data: probably a uint8 array --> expanded to int32
    :param baseline: value of the baseline
    :param underflow: value of the data below the baseline (any value with 0 are replaced with those values)
    :param overflow1: value of the data where data=255 (in the range 255-65535)
    :param overflow2: value of the data where overflow1=65535 (value >= 65535)
    :return: array of int32
    """
    in_dtype = data.dtype
    data = data.astype(numpy.int32)
    if (in_dtype.itemsize == 1) and (overflow1 is not None):
        # Use Overflow1
        print(in_dtype, overflow1)
        mask = numpy.where(data == 255)
        print(mask)
        data[mask] = overflow1
    if (in_dtype.itemsize < 4) and (overflow2 is not None):
        # Use Overflow2
        mask = numpy.where(data == 65535)
        data[mask] = overflow2
    if (underflow is None):
        data += baseline
    else:
        mask = data == 0
        data[numpy.where(mask)] = underflow
        data[numpy.logical_not(mask)] += baseline
    return data


class Bruker100Image(BrukerImage):

    DESCRIPTION = "SFRM File format used by Bruker detectors (version 100)"

    DEFAULT_EXTENSIONS = ["sfrm"]

    bpp_to_numpy = {1: numpy.uint8,
                    2: numpy.uint16,
                    4: numpy.int32}
    version = 100

    def __init__(self, data=None, header=None):
        BrukerImage.__init__(self, data, header)
        self.nover_one = self.nover_two = 0

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

        The blocks are zero padded to a multiple of 16 bits.
        """
        with self._open(fname, "rb") as infile:
            self._readheader(infile)
            rows, cols = self.shape
            npixelb = int(self.header['NPIXELB'][0])
            # you had to read the Bruker docs to know this!

            # We are now at the start of the image - assuming bruker._readheader worked
            # Get image block size from NPIXELB.
            # The total size is nbytes * nrows * ncolumns.
            
            data_size = rows* cols* npixelb
            data_size_padded = mround(data_size, 512)
            raw_data = infile.read(data_size_padded)
            data = numpy.frombuffer(raw_data[:data_size], dtype=self.bpp_to_numpy[npixelb]).reshape((rows, cols))
#             self.data = readbytestream(infile, infile.tell(), rows, cols, npixelb,
#                                        datatype="int", signed='n', swap='n')
            if npixelb > 1 and not numpy.little_endian:
                self.data = data.byteswap()
            else:
                self.data = data
            # now process the overflows
            noverfl_values = [int(f) for f in self.header['NOVERFL'].split()]
            to_merge = {"data":data,
                        "underflow": None,
                        "overflow1": None,
                        "overflow2": None,
                        "baseline": None}
            for k, nov in enumerate(noverfl_values):
                if nov <= 0:
                    continue
                if k > 2:
                    break
                if k == 0:
                    bpp = int(self.header['NPIXELB'].split()[1])
                    datatype = numpy.dtype(f"int{bpp*8}")
                else:
                    bpp = 2* k
                    datatype = self.bpp_to_numpy[bpp]
                to_read = nov * bpp
                # pad nov*bpp to a multiple of 16 bytes
                nbytes = mround(to_read, 16)

                # Multiple of 16 just above
                data_str = infile.read(nbytes)
                # ar without zeros
                ar = numpy.frombuffer(data_str[:to_read], datatype)
                if k == 0:
                    # read the set of "underflow pixels" - these will be completely disregarded for now
                    to_merge["underflow"] = ar
                elif k == 1:
                    to_merge["overflow1"] = ar
                elif k == 2:
                    to_merge["overflow2"] = ar
                else:
                    break
                logger.debug("%s bytes read + %d bytes padding" % (nov * bpp, nbytes - nov * bpp))
        # add baseline
        if noverfl_values[0] == -1:
            to_merge["baseline"] = 0
        else:
            to_merge["baseline"] = int(self.header["NEXP"].split()[2])
#             self.data[self.mask_no_undeflows] += baseline
        self.data = _merge_data(**to_merge)
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
                        line += str(str(self.nunderFlows).ljust(24, ' ') + str(self.nover_one).ljust(24) + str(self.nover_two))
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
        header = "".join(headers)
        if len(header) > 512 * self.header["HDRBLKS"]:
            tmp = ceil(len(header) / 512.0)
            self.header["HDRBLKS"] = mround(tmp, 5.0)
            for i in range(len(headers)):
                if headers[i].startswith("HDRBLKS"):
                    headers[i] = ("HDRBLKS:%s" % self.header["HDRBLKS"]).ljust(80, " ")
        else:
            self.header["HDRBLKS"] = 15
        res = pad("".join(headers), self.SPACER + "." * 78, 512 * int(self.header["HDRBLKS"]))
        return res

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
            if int(self.header["NOVERFL"].split()[0]) > 0:
                baseline = int(self.header["NEXP"].split()[2])
                tmp_data = self.data.copy()
                tmp_data[self.mask_no_undeflows] -= baseline
            else:
                tmp_data = self.data

        minusMask = numpy.where(tmp_data < 0)
        bpp = self.calc_bpp(tmp_data)
        # self.basic_translate(fname)
        limit = 2 ** (8 * bpp) - 1
        data = tmp_data.astype(self.bpp_to_numpy[bpp])
        reset = numpy.where(tmp_data >= limit)
        self.nunderFlows = int(self.header["NOVERFL"].split()[0])
        self.nover_one = len(reset[0]) + len(minusMask[0])
        self.nover_two = len(minusMask[0])
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
            bpp = 1
            # limit = 255
            nunderFlows = self.nunderFlows
            # temp_data = self.data
            read_bytes = mround(nunderFlows * bpp, 16)  # multiple of 16
            dif2usedbyts = read_bytes - (nunderFlows * bpp)
            pad_zeros = numpy.zeros(dif2usedbyts / bpp).astype(self.bpp_to_numpy[bpp])
            # flat = self.data.ravel()  # flat memory view
            # flow_pos_indexes = self.mask_undeflows
            flow_vals = (self.ar_underflows)
            # flow_vals[flow_vals<0] = 65535#limit#flow_vals[flow_vals<0]
            flow_vals_paded = numpy.hstack((flow_vals, pad_zeros)).astype(self.bpp_to_numpy[bpp])

            return flow_vals_paded  # pad(overflow, ".", 512)

    def overflows_one_byte(self):
            """
            Generate one-byte overflow table
            """
            bpp = 2
            limit = 255
            nover_one = self.nover_one
            # temp_data = self.data
            read_bytes = mround(nover_one * bpp, 16)
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
        # nover_two = self.nover_two
        read_bytes = mround(noverf * bpp, 16)
        dif2usedbyts = read_bytes - (noverf * bpp)
        pad_zeros = numpy.zeros(dif2usedbyts // bpp, dtype=self.bpp_to_numpy[bpp])
        flat = self.data.ravel()  # flat memory view

        underflow_pos = numpy.where(flat < 0)[0]
        underflow_val = flat[underflow_pos]  # [::-1]
        # underflow_val[underflow_val 0] = 65535#limit#flow_vals[flow_vals<0]

        underflow_val = underflow_val.astype(self.bpp_to_numpy[bpp])
        nderflow_val_paded = numpy.hstack((underflow_val, pad_zeros))

        return nderflow_val_paded  # pad(overflow, ".", 512)


bruker100image = Bruker100Image
