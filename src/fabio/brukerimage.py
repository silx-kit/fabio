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

Based on: openbruker,readbruker, readbrukerheader functions in the opendata
         module of ImageD11 written by Jon Wright, ESRF, Grenoble, France

Writer by Jérôme Kieffer, ESRF, Grenoble, France

"""

__authors__ = ["Henning O. Sorensen", "Erik Knudsen", "Jon Wright", "Jérôme Kieffer"]
__date__ = "05/01/2021"
__status__ = "production"
__copyright__ = "2007-2009 Risoe National Laboratory; 2010-2020 ESRF"
__licence__ = "MIT"

import logging
import numpy
from math import ceil
import os, io
import getpass
import time
logger = logging.getLogger(__name__)
from .fabioimage import FabioImage
from .fabioutils import pad, StringTypes


class BrukerImage(FabioImage):
    """
    Read and eventually write ID11 bruker (eg smart6500) images

    TODO: int32 -> float32 conversion according to the "linear" keyword.
    This is done and works but we need to check with other program that we
    are appliing the right formula and not the reciprocal one.

    """

    DESCRIPTION = "File format used by Bruker detectors (version 86)"

    # There is no extension. It is used as frame counter
    DEFAULT_EXTENSIONS = []

    bpp_to_numpy = {1: numpy.uint8,
                    2: numpy.uint16,
                    4: numpy.uint32}

    # needed if you feel like writing - see ImageD11/scripts/edf2bruker.py
    SPACER = "\x1a\x04"  # this is CTRL-Z CTRL-D
    HEADERS_KEYS = ["FORMAT",  # Frame format. Always “86” or "100" for Bruker-format frames.
                    "VERSION",  # Header version #, such as: 1 to 17 (6 is obsolete).
                    "HDRBLKS",  # Header size in 512-byte blocks, such as 10 or 15. Determines where the image block begins.
                    "TYPE",  # String indicating kind of data in the frame. Used to determine if a spatial correction table was applied to the frame imag
                    "SITE",  # Site name
                    "MODEL",  # Diffractometer model
                    "USER",  # Username
                    "SAMPLE",  # Sample ID,
                    "SETNAME",  # Basic data set name
                    "RUN",  # Run number within the data set, usually starts at 0, but 1 for APEX2.
                    "SAMPNUM",  # Specimen number within the data set
                    "TITLE",  # User comments (8 lines)
                    "NCOUNTS",  # Total frame counts
                    "NOVERFL",  # Number of overflows when compression frame.
                    "MINIMUM",  # Minimum counts in a pixel (uncompressed value)
                    "MAXIMUM",  # Maximum counts in a pixel (uncompressed value)
                    "NONTIME",  # Number of on-time events
                    "NLATE",  # Number of late events. Always zero for many detectors.
                    "FILENAM",  # (Original) frame filename
                    "CREATED",  # Date and time of creation
                    "CUMULAT",  # Accumulated frame exposure time in seconds
                    "ELAPSDR",  # Requested time for last exposure in seconds
                    "ELAPSDA",  # Actual time for last exposure in seconds.
                    "OSCILLA",  # Nonzero if acquired by oscillation
                    "NSTEPS",  # steps or oscillations in this frame
                    "RANGE",  # Scan range in decimal degrees (unsigned)
                    "START",  # Starting scan angle value, decimal degrees
                    "INCREME",  # Scan angle increment between frames (signed)
                    "NUMBER",  # Sequence number of this frame in series, usually starts at 0, but 1 for APEX2
                    "NFRAMES",  # Total number of frames in the series
                    "ANGLES",  # Diffractometer angles in Eulerian space ( 2T, OM, PH, CH).
                    "NOVER64",  # Number of pixels > 64K (actually LinearThreshold value)
                    "NPIXELB",  # Number of bytes/pixel, such as 1, 2, or 4.
                    "NROWS",  # Number of rasters in frame, such as 512, 1024, 2048, or 4096
                    "NCOLS",  # Number of pixels/raster, such as 512, 1024, 2048 or 4096
                    "WORDORD",  # Order of bytes in word (0=LSB first)
                    "LONGORD",  # Order of words in a longword (0=LSW first)
                    "TARGET",  # X-ray target material: Cu, Mo, Ag, Fe, Cr, Co, Ni, W, Mn, or other.
                    "SOURCEK",  # X-ray source voltage in kV
                    "SOURCEM",  # X-ray source current in mA
                    "FILTER",  # Filter/monochromator setting: Such as: Parallel, graphite, Ni Filter, C Filter, Zr Filter,Cross coupled Goebel Mirrors ...
                    "CELL",  # Unit cell A,B,C,ALPHA,BETA,GAMMA
                    "MATRIX",  # 9R Orientation matrix (P3 conventions)
                    "LOWTEMP",  # Low temp flag.
                    "TEMP",  # set temperature
                    "HITEMP",  # Acquired at high temperature
                    "ZOOM",  # Zoom: Xc, Yc, Mag used for HI-STAR detectors: 0.5 0.5 1.0
                    "CENTER",  # X, Y of direct beam at 2-theta = 0. These are raw center for raw frames and unwarped center for unwarped frames.
                    "DISTANC",  # Sample-detector distance, cm (see CmToGrid value) Adds: Sample-detector grid/phosphor distance, cm
                    "TRAILER",  # Byte pointer to trailer info
                    "COMPRES",  # Compression scheme ID, if any. Such as: NONE, LINEAR (Linear scale, offset for pixel values, typically 1.0, 0.0).
                    "LINEAR",  # Linear scale (1.0 0.0 for no change; 0.1 0 for divided by 10...)
                    "PHD",  # Discriminator: Pulse height settings. X100 and X1000 only. Stores CCD phosphor efficiency (first field).
                    "PREAMP",  # Preamp gain setting. X100 and X1000 only. SMART: Stores Roper CCD gain table index value.
                    "CORRECT",  # Flood table correction filename, UNKNOWN or LINEAR.
                    "WARPFIL",  # Brass plate correction filename, UNKNOWN or LINEAR. Note: A filename here does NOT mean that spatial correction was performed. See TYPE and string “UNWARP” to determine that.
                    "WAVELEN",  # Wavelengths (average, a1, a2)
                    "MAXXY",  # X,Y pixel # of maximum counts (from lower corner of 0,0)
                    "AXIS",  # Scan axis ib Eulerian space (1-4 for 2-theta, omega, phi, chi) (0 =none, 2 = default).
                    "ENDING",  # Actual goniometer angles at end of frame in Eulerian space.
                    "DETPAR",  # Detector position corrections (dX,dY,dDist,Pitch,Roll,Yaw)
                    "LUT",  # Recommended display lookup table
                    "DISPLIM",  # Recommended display limits
                    "PROGRAM",  # Name and version of program writing frame, such as:
                    "ROTATE",  # Non zero if acquired by rotation of phi during scan (or oscilate)
                    "BITMASK",  # File name of active pixel mask associated with this frame or $NULL
                    "OCTMASK",  # Octagon mask parameters to use if BITMASK=$null. Min X, Min X+Y, Min Y, Max X-Y, Max X, Max X+Y, Max Y, Max Y-X.
                    "ESDCELL",  # Unit cell parameter standard deviations
                    "DETTYPE",  # Detector or CCD chip type (as displayed on CEU). Default is MULTIWIRE but UNKNOWN is advised, can contain PIXPERCM: CMTOGRID:
                    "NEXP",  # Number of exposures: 1=single, 2=correlated sum.32 for most ccds, and 64 for 2K ccds.
                    "CCDPARM",  # CCD parameters: readnoise, e/ADU, e/photon, bias, full scale
                    "BIS",  # Potential full linear scale if rescan and attenuator used.
                    "CHEM",  # Chemical formula in CIFTAB string, such as “?”
                    "MORPH",  # Crystal morphology in CIFTAB string, such as “?”
                    "CCOLOR",  # Crystal color in CIFTAB string, such as “?”
                    "CSIZE",  # Crystal dimensions (3 ea) in CIFTAB string, such as “?”
                    "DNSMET",  # Density measurement method in CIFTAB string, such as “?”
                    "DARK",  # Name of dark current correction or NONE.
                    "AUTORNG",  # Auto-ranging: gain, high-speed time, scale, offset, full linear scale Note: If full linear scale is zero, then CCDPARM full scale is the full linear scale (BIS frames).
                    "ZEROADJ",  # Goniometer zero corrections (refined in least squares)
                    "XTRANS",  # Crystal XYZ translations (refined in least squares)
                    "HKL&XY",  # HKL and pixel XY for reciprocal space scan. GADDS only.
                    "AXES2",  # Diffractometer setting linear axes (4 ea). (X, Y, Z, Aux)
                    "ENDING2",  # Actual goniometer linear axes @ end of frame. (X, Y, Z, Aux)
                    "FILTER2",  # Monochromator 2-theta angle and monochromator roll angle. v15: Adds beam tilt angle and attenuator factor.
                    "LEPTOS",  # String for LEPTOS.
                    "CFR",  # Only in 21CFRPart11 mode, writes the checksum for header and image (2str).]
                    ]
    version = 86

    def __init__(self, data=None, header=None):
        FabioImage.__init__(self, data, header)
        self.__bpp_file = None
        self.__headerstring__ = ""

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
        self.__headerstring__ = infile.read(blocksize * nhdrblks).decode("ASCII")
        self.header = self.check_header()
        for i in range(0, nhdrblks * blocksize, line):
            if self.__headerstring__[i: i + line].find(":") > 0:
                key, val = self.__headerstring__[i: i + line].split(":", 1)
                key = key.strip()  # remove the whitespace (why?)
                val = val.strip()
                if key in self.header:
                    # append lines if key already there
                    self.header[key] = self.header[key] + os.linesep + val
                else:
                    self.header[key] = val
        # we must have read this in the first 5*512 bytes.
        nhdrblks = int(self.header.get('HDRBLKS', 5))
        self.header['HDRBLKS'] = nhdrblks
        # Now read in the rest of the header blocks, appending
        self.__headerstring__ += infile.read(blocksize * (nhdrblks - 5)).decode("ASCII")
        for i in range(5 * blocksize, nhdrblks * blocksize, line):
            if self.__headerstring__[i: i + line].find(":") > 0:  # as for first 512 bytes of header
                key, val = self.__headerstring__[i: i + line].split(":", 1)
                key = key.strip()
                val = val.strip()
                if key in self.header:
                    self.header[key] = self.header[key] + os.linesep + val
                else:
                    self.header[key] = val
        # make a (new) header item called "datastart"
        self.header['datastart'] = blocksize * nhdrblks

        # set the image dimensions
        shape = int(self.header['NROWS'].split()[0]), int(self.header['NCOLS'].split()[0])
        self._shape = shape
        self.version = int(self.header.get('FORMAT', "86"))

    def read(self, fname, frame=None):
        """
        Read in and unpack the pixels (including overflow table
        """
        with self._open(fname, "rb") as infile:
            try:
                self._readheader(infile)
            except Exception as err:
                raise RuntimeError("Unable to parse Bruker headers: %s" % err)

            rows, cols = self._shape

            try:
                # you had to read the Bruker docs to know this!
                npixelb = int(self.header['NPIXELB'])
            except Exception:
                errmsg = "length " + str(len(self.header['NPIXELB'])) + "\n"
                for byt in self.header['NPIXELB']:
                    errmsg += "char: " + str(byt) + " " + str(ord(byt)) + "\n"
                logger.warning(errmsg)
                raise RuntimeError(errmsg)

            data = numpy.frombuffer(infile.read(rows * cols * npixelb), dtype=self.bpp_to_numpy[npixelb]).copy()
            if not numpy.little_endian and data.dtype.itemsize > 1:
                data.byteswap(True)

            # handle overflows
            nov = int(self.header['NOVERFL'])
            if nov > 0:  # Read in the overflows
                # need at least int32 sized data I guess - can reach 2^21
                data = data.astype(numpy.uint32)
                # 16 character overflows:
                #      9 characters of intensity
                #      7 character position
                for _ in range(nov):
                    ovfl = infile.read(16)
                    intensity = int(ovfl[0: 9])
                    position = int(ovfl[9: 16])
                    data[position] = intensity
        # infile.close()

        # Handle Float images ...
        if "LINEAR" in self.header:
            try:
                slope, offset = self.header["LINEAR"].split(None, 1)
                slope = float(slope)
                offset = float(offset)
            except Exception:
                logger.warning("Error in converting to float data with linear parameter: %s" % self.header["LINEAR"])
                slope = 1
                offset = 0
            if (slope != 1) or (offset != 0):
                # TODO: check that the formula is OK, not reverted.
                logger.warning("performing correction with slope=%s, offset=%s (LINEAR=%s)" % (slope, offset, self.header["LINEAR"]))
                data = (data * slope + offset).astype(numpy.float32)
        self.data = data.reshape(self._shape)

        self.resetvals()
        return self

    def write(self, fname):
        """
        Write a bruker image

        """
        if numpy.issubdtype(self.data.dtype, numpy.floating):
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
        bpp = self.calc_bpp(tmp_data)
        self.basic_translate(fname)
        limit = 2 ** (8 * bpp) - 1
        data = tmp_data.astype(self.bpp_to_numpy[bpp])
        reset = numpy.where(tmp_data >= limit)
        data[reset] = limit
        if not numpy.little_endian and bpp > 1:
            # Bruker enforces little endian
            data.byteswap(True)
        with self._open(fname, "wb") as bruker:
            bruker.write(self.gen_header().encode("ASCII"))
            if isinstance(bruker, io.BufferedWriter):
                data.tofile(bruker)
            else:
                bruker.write(data.tobytes())
            bruker.write(self.gen_overflow().encode("ASCII"))

    def calc_bpp(self, data=None, max_entry=4096):
        """
        Calculate the number of byte per pixel to get an optimal overflow table.

        :return: byte per pixel
        """
        if data is None:
            data = self.data
        if self.__bpp_file is None:
            for i in [1, 2]:
                overflown = (data >= (2 ** (8 * i) - 1))
                if overflown.sum() < max_entry:
                    self.__bpp_file = i
                    break
            else:
                self.__bpp_file = 4
        return self.__bpp_file

    def gen_header(self):
        """
        Generate headers (with some magic and guesses)
        """
        headers = []
        for key in self.HEADERS_KEYS:
            if key in self.header:
                value = self.header[key]
                line = key.ljust(7) + ":"
                if type(value) in StringTypes:
                    if os.linesep in value:
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
            self.header["HDRBLKS"] = int(ceil(tmp / 5.0) * 5.0)
            for i in range(len(headers)):
                if headers[i].startswith("HDRBLKS"):
                    headers[i] = headers.append(("HDRBLKS:%s" % self.header["HDRBLKS"]).ljust(80, " "))
        res = pad("".join(headers), self.SPACER + "." * 78, 512 * int(self.header["HDRBLKS"]))
        return res

    def gen_overflow(self):
        """
        Generate an overflow table
        """
        limit = 2 ** (8 * self.calc_bpp()) - 1
        flat = self.data.ravel()  # flat memory view
        overflow_pos = numpy.where(flat >= limit)[0]  # list of indexes
        overflow_val = flat[overflow_pos]
        overflow = "".join(["%09i%07i" % (val, pos) for pos, val in zip(overflow_pos, overflow_val)])
        return pad(overflow, ".", 512)

    def basic_translate(self, fname=None):
        """
        Does some basic population of the headers so that the writing is possible
        """
        if "FORMAT" not in self.header:
            self.header["FORMAT"] = "86"
        if "HDRBLKS" not in self.header:
            self.header["HDRBLKS"] = 5
        if "TYPE" not in self.header:
            self.header["TYPE"] = "UNWARPED"
        if "USER" not in self.header:
            self.header["USER"] = getpass.getuser()
        if "FILENAM" not in self.header:
            self.header["FILENAM"] = "%s" % fname
        if "CREATED" not in self.header:
            self.header["CREATED"] = time.ctime()
        if "NOVERFL" not in self.header:
            self.header["NOVERFL"] = "0"
#        if not "NPIXELB" in self.header:
        self.header["NPIXELB"] = self.calc_bpp()
        # if not "NROWS" in self.header:
        self.header["NROWS"] = self.data.shape[0]
        # if not "NCOLS" in self.header:
        self.header["NCOLS"] = self.data.shape[1]
        if "WORDORD" not in self.header:
            self.header["WORDORD"] = "0"
        if "LONGORD" not in self.header:
            self.header["LONGORD"] = "0"


brukerimage = BrukerImage
