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
# THE SOFTWARE

from __future__ import with_statement, print_function

__authors__ = ["V. Valls"]
__license__ = "MIT"
__date__ = "07/02/2018"

import re
import logging
from . import tifimage


_logger = logging.getLogger(__name__)


class PilatusTiffFrame(tifimage.TiffFrame):
    """Frame container for TIFF format generated by a Pilatus detector"""

    def __init__(self, data, tiff_header, pilatus_header):
        super(PilatusTiffFrame, self).__init__(data, tiff_header)
        self.pilatus_header = pilatus_header

    @property
    def header(self):
        """Default header exposed by fabio"""
        return self.pilatus_header


class PilatusImage(tifimage.TifImage):
    """ Read in Pilatus format, also
        pilatus images, including header info """

    DESCRIPTION = "Pilatus file format based on Tiff"

    DEFAULT_EXTENSIONS = ["tif", "tiff"]

    _keyvalue_spliter = re.compile("\s*(?:[,:=]\s*)?")
    """It allow to split the first white space, colon, coma, or equal
    character and remove white spaces around"""

    @staticmethod
    def split(inp, sep=" ", cnt=None):
        """It allow to split the first white space, colon, coma, or equal
        character and remove white spaces around

        Rather inefficient but works in python 3.7 unlike _keyvalue_spliter
        
        :param inp: input string
        :param sep: string with all separators
        :param cnt: number of segment in output
        """
        res = []
        tmp = ""
        for i,v in enumerate(inp):
            if v in sep:
                if tmp:
                    res.append(tmp)
                    tmp = ""
            else:
                tmp+=v
            if cnt and (len(res)>=cnt):
                res.append(inp[i:].strip(sep))
                break
        return res
        
    def _create_pilatus_header(self, tiff_header):
        """
        Parse Pilatus header from a TIFF header.

        The Pilatus header is stored in the metadata ImageDescription (tag 270)
        as an ASCII text which looks like:

        .. block-code:: python

            imageDescription = '# Pixel_size 172e-6 m x 172e-6 m\r\n'\
                '# Silicon sensor, thickness 0.000320 m\r\n# Exposure_time 90.000000 s\r\n'\
                '# Exposure_period 90.000000 s\r\n# Tau = 0 s\r\n'\
                '# Count_cutoff 1048574 counts\r\n# Threshold_setting 0 eV\r\n'\
                '# Gain_setting not implemented (vrf = 9.900)\r\n'\
                '# N_excluded_pixels = 0\r\n# Excluded_pixels: (nil)\r\n'\
                '# Flat_field: (nil)\r\n# Trim_directory: (nil)\r\n\x00'

        :rtype: OrderedDict
        """
        if "imageDescription" not in tiff_header:
            # It is not a Pilatus TIFF image
            raise IOError("Image is not a Pilatus image")

        header = self.check_header()

        description = tiff_header["imageDescription"]
        for line in description.split("\n"):
            index = line.find('# ')
            if index == -1:
                if line.strip(" \x00") != "":
                    # If it is not an empty line
                    _logger.debug("Pilatus header line '%s' misformed. Skipped", line)
                continue

            line = line[2:].strip()
            if line == "":
                # empty line
                continue

            result = self.split(line, " :=", 1)
            if len(result) != 2:
                _logger.debug("Pilatus header line '%s' misformed. Skipped", line)
                continue

            key, value = result
            header[key] = value

        return header

    def _create_frame(self, image_data, tiff_header):
        """Create exposed data from TIFF information"""
        pilatus_header = self._create_pilatus_header(tiff_header)
        frame = PilatusTiffFrame(image_data, tiff_header, pilatus_header)
        return frame


pilatusimage = PilatusImage
