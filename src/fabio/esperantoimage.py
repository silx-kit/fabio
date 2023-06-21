# coding: utf-8
#
#    Project: X-ray image reader
#             https://github.com/silx-kit/fabio
#
#    Copyright (C) European Synchrotron Radiation Facility, Grenoble, France
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

__authors__ = ["Florian Plaswig", "Jérôme Kieffer"]
__license__ = "MIT"
__copyright__ = "2019-2020 ESRF"
__date__ = "09/02/2023"

import io
from collections import OrderedDict
import logging
logger = logging.getLogger(__name__)
import numpy
from .fabioimage import FabioImage
from .compression import agi_bitfield


class EsperantoImage(FabioImage):
    """FabIO image class for Esperanto image files
    """
    DESCRIPTION = "CrysAlis Pro Esperanto file format"
    DEFAULT_EXTENSIONS = [".eseperanto", ".esper"]
    HEADER_SEPARATOR = "\x0d\x0a"
    HEADER_END = b"\x0d\x1a"
    HEADER_LINES = 25
    HEADER_WIDTH = 256
    VALID_FORMATS = ("AGI_BITFIELD", "4BYTE_LONG")
    DUMMY = 0  # Value to fill empty regions with when padding

    HEADER_KEYS = OrderedDict([("IMAGE", "lnx lny lbx lby spixelformat"),
                               ("SPECIAL_CCD_1", "delectronsperadu ldarkcorrectionswitch lfloodfieldcorrectionswitch/mode dsystemdcdb2gain ddarksignal dreadnoiserms"),
                               ("SPECIAL_CCD_2", "ioverflowflag ioverflowafterremeasureflag inumofdarkcurrentimages inumofmultipleimages loverflowthreshold"),
                               ("SPECIAL_CCD_3", "ldetector_descriptor lisskipcorrelation lremeasureturbomode bfsoftbinningflag bflownoisemodeflag"),
                               ("SPECIAL_CCD_4", "lremeasureinturbo_done lisoverflowthresholdchanged loverflowthresholdfromimage lisdarksignalchanged lisreadnoisermschanged lisdarkdone lisremeasurewithskipcorrelation lcorrelationshift"),
                               ("SPECIAL_CCD_5", "dblessingrej ddarksignalfromimage dreadnoisermsfromimage dtrueimagegain"),
                               ("TIME", "dexposuretimeinsec doverflowtimeinsec doverflowfilter"),
                               ("MONITOR", "lmon1 lmon2 lmon3 lmon4"),
                               ("PIXELSIZE", "drealpixelsizex drealpixelsizey dsithicknessmmforpixeldetector"),
                               ("TIMESTAMP", "timestampstring"),
                               ("GRIDPATTERN", "filename"),
                               ("STARTANGLESINDEG", "dom_s dth_s dka_s dph_s"),
                               ("ENDANGLESINDEG", "dom_e dth_e dka_e dph_e"),
                               ("GONIOMODEL_1", "dbeam2indeg dbeam3indeg detectorrotindeg_x detectorrotindeg_y detectorrotindeg_z dxorigininpix dyorigininpix dalphaindeg dbetaindeg ddistanceinmm"),
                               ("GONIOMODEL_2", "dzerocorrectionsoftindeg_om dzerocorrectionsoftindeg_th dzerocorrectionsoftindeg_ka dzerocorrectionsoftindeg_ph"),
                               ("WAVELENGTH", "dalpha1 dalpha2 dalpha12 dbeta1"),
                               ("MONOCHROMATOR", "ddvalue-prepolfac orientation-type"),
                               ("ABSTORUN", "labstorunscale"),
                               ("HISTORY", "historystring")])

    def __init__(self, *arg, **kwargs):
        """
        Generic constructor
        """
        self._data = None
        FabioImage.__init__(self, *arg, **kwargs)
        self.format = "AGI_BITFIELD"  # "4BYTE_LONG" is the other option

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        """Esperanto accepts only images square with size a multiple of 4
        and limit the size to 256-4096 
        """
        if value is None:
            self._data = value
            return
        assert isinstance(value, numpy.ndarray)
        old_shape = value.shape
        size = max(old_shape)
        padded_size = (size + 3) & ~3
        padded_size = numpy.clip(padded_size, 256, 4096)
        new_shape = (padded_size, padded_size)
        if not numpy.issubdtype(value.dtype, numpy.integer):
            logger.info("Esperanto accepts only integer data, rounding")
            value = numpy.round(value)
        value = value.astype(numpy.int32)

        if old_shape != new_shape:
            logger.info("Padding image to be square, multiple of 4 and of size between 256 and 4096")
            self._data = numpy.zeros(new_shape, dtype=numpy.int32) + self.DUMMY
            # Nota: center horizontally, not vertically (!?)
            shift = max((new_shape[1] - old_shape[1]) // 2, 0)

            self._data[:min(old_shape[0], new_shape[0]),
                       shift:min(shift + old_shape[1], new_shape[1])] = value
        else:
            self._data = value

    def _readheader(self, infile):
        """
        Read and decode the header of an image:

        :param infile: Opened python file (can be stringIO or bipped file)
        """
        self.header = self.check_header()

        # read the first line of the header
        top_line = infile.read(self.HEADER_WIDTH).decode('ascii')
        if not top_line[-2:] == self.HEADER_SEPARATOR:
            raise RuntimeError("Unable to read esperanto header: Invalid format of first line")
        words = top_line.split()
        try:
            self.HEADER_LINES = int(words[5])
        except Exception as err:
            raise RuntimeError("Unable to determine header size: %s" % err)
        assert self.HEADER_WIDTH == int(words[8]), "Line length match"
        self.header["ESPERANTO FORMAT"] = ' '.join(words[2:])
        self.header["format"] = int(words[2])

        # read the remaining lines
        for line_num in range(1, self.HEADER_LINES):
            line = infile.read(self.HEADER_WIDTH).decode('ascii')
            if not line[-2] == self.HEADER_SEPARATOR[0]:
                raise RuntimeError("Unable to read esperanto header: Invalid format of line %d." % (line_num + 1))
            words = line.split()
            if not words:
                continue
            key = words[0]
            if len(key) == 1 and ord(key) < 32:
                continue
            self.header[key] = ' '.join(words[1:])
            if key not in self.HEADER_KEYS:
                logger.warning("Unable to read esperanto header: Invalid Key %s in line %d." % (key, line_num))
            else:  # try to interpret
                if key in ("HISTORY", "TIMESTAMP"):
                    self.header[self.HEADER_KEYS[key]] = " ".join(words[1:]).strip('"')
                else:
                    lower_keys = self.HEADER_KEYS[key].split()

                    for k, v in zip(lower_keys, words[1:]):
                        if k[0] in "lib":
                            try:
                                value = int(v)
                            except:
                                value = v
                        elif k[0] == "d":
                            try:
                                value = float(v)
                            except:
                                value = v
                        else:
                            value = v.strip('"')
                        self.header[k] = value

        width = self.header["lnx"]
        height = self.header["lny"]
        if 256 > width > 4096 or width % 4 != 0 or 256 > height > 4096 or height % 4 != 0:
            logger.warning("The dimensions of the image is (%i, %i) but they should only be between 256 and 4096 and a multiple of 4. This might cause compatibility issues.")

        self.shape = (height, width)

        self.format = self.header["spixelformat"]
        self._dtype = "int32"

    def read(self, fname, frame=None):
        """
        Try to read image

        :param fname: name of the file
        :param frame: number of the frame
        """

        self.resetvals()
        with self._open(fname) as infile:
            self._readheader(infile)

            if self.format == "4BYTE_LONG":
                try:
                    pixelsize = 4
                    pixelcount = self.shape[0] * self.shape[1]
                    data = numpy.frombuffer(infile.read(pixelsize * pixelcount), dtype=self._dtype)
                    self.data = numpy.reshape(data, self.shape)
                except Exception as err:
                    raise RuntimeError("Exception while reading pixel data %s." % err)
            elif self.format == "AGI_BITFIELD":
                raw_data = infile.read()
                try:
                    self.data = agi_bitfield.decompress(raw_data, self.shape)
                except Exception as err:
                    raise RuntimeError("Exception while decompressing pixel data %s." % err)
            else:
                raise RuntimeError("Format not supported %s. Valid formats are %s" % (self.format, self.VALID_FORMATS))

        return self

    def _formatheaderline(self, line):
        "Return one line as ASCII bytes padded with end of line"
        assert len(line) <= self.HEADER_WIDTH - len(self.HEADER_SEPARATOR)
        return (line.ljust(self.HEADER_WIDTH - len(self.HEADER_SEPARATOR), " ") + self.HEADER_SEPARATOR).encode("ASCII")

    def _update_header(self):
        """
        Upper-cases headers are directly written into the ASCII header of the file.
        This method updates them according to values found in lower-case header (if any)
        
        As a consequence, unforeseen headers are simply discarded.  
        """
        if "ESPERANTO FORMAT" not in self.header:  # default format
            self.header["ESPERANTO FORMAT"] = "1 CONSISTING OF   25 LINES OF   256 BYTES EACH"
        else:
            self.header["ESPERANTO FORMAT"] = "%s CONSISTING OF   %s LINES OF   %s BYTES EACH" % (self.header["format"], self.HEADER_LINES, self.HEADER_WIDTH)
        self.header["lny"], self.header["lnx"] = self.data.shape
        self.header["spixelformat"] = self.format
        if "lbx" not  in self.header:
            self.header["lbx"] = 1
        if "lby" not  in self.header:
            self.header["lby"] = 1

        for key, value in self.HEADER_KEYS.items():
            updated = ""
            for lower_key in value.split():
                if lower_key[0] in "ldib":
                    updated += '%s ' % self.header.get(lower_key, 0)
                else:
                    updated += '"%s" ' % self.header.get(lower_key, "")
            self.header[key] = updated.strip()

    def write(self, fname):
        """
        Write an image

        :param fname: name of the file
        """

        # create header
        self._update_header()
        bytes_header = self._formatheaderline("ESPERANTO FORMAT   " + self.header["ESPERANTO FORMAT"])
        for key in self.HEADER_KEYS:
            bytes_header += self._formatheaderline(key + ' ' + self.header[key])
        if len(self.HEADER_KEYS) + 1 < self.HEADER_LINES:
            bytes_header += self._formatheaderline("") * (self.HEADER_LINES - len(self.HEADER_KEYS) - 1)
        bytes_header = bytes_header[:-len(self.HEADER_SEPARATOR)] + self.HEADER_END
        with self._open(fname, "wb") as outfile:
            outfile.write(bytes_header)
            if self.format == "4BYTE_LONG":
                if isinstance(outfile, io.BufferedWriter):
                    self.data.tofile(outfile)
                else:
                    outfile.write(self.data.tobytes())
            elif self.format == "AGI_BITFIELD":
                if agi_bitfield._compress is not None:
                    outfile.write(agi_bitfield._compress(self.data))
                else:
                    outfile.write(agi_bitfield.compress(self.data))
            else:
                raise RuntimeError("Format not supported %s." % self.format)


# This is for compatibility with old code:
esperantoimage = EsperantoImage
