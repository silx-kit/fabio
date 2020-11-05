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
__date__ = "05/11/2020"

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
        self.format = ""

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
            self._data = numpy.zeros(new_shape, dtype=numpy.int32)
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
        top_line = infile.read(256).decode('ascii')

        if not top_line[-2:] == self.HEADER_SEPARATOR:
            raise RuntimeError("Unable to read esperanto header: Invalid format of first line")
        words = top_line.split()
        try:
            header_line_count = int(words[5])
        except Exception as err:
            raise RuntimeError("Unable to determine header size: %s" % err)

        self.header["ESPERANTO_FORMAT"] = ' '.join(words[2:])
        self.header["format"] = int(words[2])

        # read the remaining lines
        for line_num in range(1, header_line_count):
            line = infile.read(256).decode('ascii')
            if not line[-2] == self.HEADER_SEPARATOR[0]:
                raise RuntimeError("Unable to read esperanto header: Invalid format of line %d." % (line_num + 1))

            line = line.rstrip()
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
                lower_keys = self.HEADER_KEYS[key].split()

                for k, v in zip(lower_keys, words[1:]):
                    if k.startswith("l") or k.startswith("i"):
                        try:
                            value = int(v)
                        except:
                            value = v
                    elif k.startswith("d"):
                        try:
                            value = float(v)
                        except:
                            value = v
                    elif k.startswith("s"):
                        try:
                            value = v.strip('"')
                        except:
                            value = v
                    else:
                        value = v
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
                    data = numpy.frombuffer(infile.read(pixelsize * pixelcount), dtype=self._dtype).copy()
                    self.data = numpy.reshape(data, self.shape)
                except Exception as err:
                    raise RuntimeError("Exception while reading pixel data %s." % err)
            elif self.format == "AGI_BITFIELD":
                self.raw_data = infile.read()
                try:
                    print(self.shape, type(self.raw_data))
                    self.data = agi_bitfield.decompress(self.raw_data, self.shape)
                except Exception as err:
                    raise RuntimeError("Exception while decompressing pixel data %s." % err)
            else:
                raise RuntimeError("Format not supported %s." % self.format)

        return self

    def _formatheaderline(self, line):
        assert len(line) <= 254
        line += ' ' * (254 - len(line))
        line += self.HEADER_SEPARATOR
        return line.encode("ASCII")

    def write(self, fname):
        """
        Write an image

        :param fname: name of the file
        """

        # create header
        if "IMAGE" not in self.header:  # create image entry
            dtype_info = '"%s"' % self.format
            dx, dy = self.shape

            self.header["IMAGE"] = "%d %d 1 1 %s" % (dx, dy, dtype_info)

        else:  # update image entry
            dtype_info = '"4BYTE_LONG"'
            dx, dy = self.shape
            split = self.header["IMAGE"].split(' ')

            split[0] = str(dy)
            split[1] = str(dx)
            split[4] = str(dtype_info)

            self.header["IMAGE"] = ' '.join(split)

        if 256 > dx > 4096 or dx % 4 != 0 or 256 > dy > 4096 or dy % 4 != 0:
            logger.warning("The dimensions of the image is (%i, %i) but they should only be between 256 and 4096 and a multiple of 4. This might cause compatibility issues.")

        if "ESPERANTO_FORMAT" not in self.header:  # default format
            self.header["ESPERANTO_FORMAT"] = "ESPERANTO FORMAT 1.1"

        self.header = dict(filter(self.header, lambda elem: elem[0] in self.HEADER_KEYS))

        header_top = self._formatheaderline("%s CONSISTING OF %d LINES OF 256 BYTE EACH" %
                                                (self.header["ESPERANTO_FORMAT"], len(self.header)))
        HEADER = header_top
        for header_key in self.header:
            if header_key == "ESPERANTO_FORMAT":  # or header_key not in self.HEADER_KEYS:
                continue
            header_val = self.header[header_key]
            HEADER += self._formatheaderline(header_key + ' ' + header_val)

        with self._open(fname, "wb") as outfile:
            outfile.write(HEADER)
            if self.format == "4BYTE_LONG":
                outfile.write(self.data.tobytes())
            elif self.format == "AGI_BITFIELD":
                outfile.write(agi_bitfield.compress(self.data))
            else:
                raise RuntimeError("Format not supported %s." % self.format)


# This is not compatibility with old code:
esperantoimage = EsperantoImage
