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

from __future__ import with_statement, print_function, division

__authors__ = ["Florian Plaswig"]
__license__ = "MIT"
__copyright__ = "ESRF"
__date__ = "10/10/2019"

import logging
logger = logging.getLogger(__name__)
import numpy
from .fabioimage import FabioImage
from .compression import agi_bitfield


class EsperantoImage(FabioImage):
    """FabIO image class for Esperanto image files
    """

    DESCRIPTION = "CrysAlis Pro Esperanto file format "

    DEFAULT_EXTENSIONS = [".eseperanto", ".esper"]

    HEADER_SEPARATOR = "\x0d\x0a"

    HEADER_KEYS = ["IMAGE",
                   "SPECIAL_CCD_1",
                   "SPECIAL_CCD_2",
                   "SPECIAL_CCD_3",
                   "SPECIAL_CCD_4",
                   "SPECIAL_CCD_5",
                   "TIME",
                   "MONITOR",
                   "AUTORUN",
                   "PIXELSIZE",
                   "TIMESTAMP",
                   "GRIDPATTERN",
                   "STARTANGLESINDEG",
                   "ENDANGLESINDEG",
                   "GONIOMODEL_1",
                   "GONIOMODEL_2",
                   "WAVELENGHTH",
                   "MONOCHROMATOR",
                   "HISTORY",
                   "ESPERANTO_FORMAT",
                   "WAVELENGTH",
                   "ABSTORUN"]

    def __init__(self, *arg, **kwargs):
        """
        Generic constructor
        """
        FabioImage.__init__(self, *arg, **kwargs)
        self.format = ""

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

        try:
            header_line_count = int(top_line.split(' ')[5])
        except Exception as err:
            raise RuntimeError("Unable to determine header size: %s" % err)

        self.header["ESPERANTO_FORMAT"] = ' '.join(top_line.split(' ')[:2])

        # read the remaining lines
        for line_num in range(1, header_line_count):
            line = infile.read(256).decode('ascii')

            if not line[-2:] == self.HEADER_SEPARATOR:
                raise RuntimeError("Unable to read esperanto header: Ivalid format of line %d." % (line_num + 1))

            line = line.rstrip()
            split_line = line.split(' ')
            key = split_line[0]
            if key.rstrip() == '':
                continue

            # if key not in self.HEADER_KEYS:
            #     raise RuntimeError("Unable to read esperanto header: Invalid Key %s in line %d." % (key, line_num))

            self.header[key] = ' '.join(split_line[1:])

        # extract necessary data
        if "IMAGE" not in self.header:
            raise RuntimeError("No IMAGE entry found in header.")

        try:
            image_data = self.header["IMAGE"].split(' ')

            width = int(image_data[0])
            height = int(image_data[1])
        except Exception as err:
            raise RuntimeError("Unable to determine dimensions of file: %s" % err)

        if 256 > width > 4096 or width % 4 != 0 or 256 > height > 4096 or height % 4 != 0:
            logger.warning("The dimensions of the image is (%i, %i) but they should only be between 256 and 4096 and a multiple of 4. This might cause compatibility issues.")

        self.shape = (height, width)

        self.format = self.header["IMAGE"].split(' ')[4][1:-1]
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
                logger.warning("AGI_BITFIELD decompression is known to be apporximative ... use those data with caution !")
                try:
                    data = agi_bitfield.decompress(self.raw_data, self.shape)
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
        if "IMAGE" not in self.header: # create image entry
            dtype_info = '"%s"' % self.format
            dx, dy = self.shape

            self.header["IMAGE"] = "%d %d 1 1 %s" % (dx, dy, dtype_info)

        else: # update image entry
            dtype_info = '"4BYTE_LONG"'
            dx, dy = self.shape
            split = self.header["IMAGE"].split(' ')

            split[0] = str(dy)
            split[1] = str(dx)
            split[4] = str(dtype_info)

            self.header["IMAGE"] = ' '.join(split)

        if 256 > dx > 4096 or dx % 4 != 0 or 256 > dy > 4096 or dy % 4 != 0:
            logger.warning("The dimensions of the image is (%i, %i) but they should only be between 256 and 4096 and a multiple of 4. This might cause compatibility issues.")

        if "ESPERANTO_FORMAT" not in self.header: # default format
            self.header["ESPERANTO_FORMAT"] = "ESPERANTO FORMAT 1.1"

        self.header = dict(filter(self.header, lambda elem: elem[0] in self.HEADER_KEYS))

        header_top = self._formatheaderline("%s CONSISTING OF %d LINES OF 256 BYTE EACH" %
                                                (self.header["ESPERANTO_FORMAT"], len(self.header)))
        HEADER = header_top
        for header_key in self.header:
            if header_key == "ESPERANTO_FORMAT": #or header_key not in self.HEADER_KEYS:
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
