# coding: utf-8
#
#    Project: FabIO X-ray image reader
#
#    Copyright (C) 2017 Cornell High Energy Synchrotron Source
#                       Ithaca (New York, USA)
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
Author:
........
* Jesse Hopkins:
  Cornell High Energy Synchrotron Source;
  Ithaca (New York, USA)

mpaimage can read ascii and binary .mpa (multiwire) files
"""

import logging
import numpy
from .fabioimage import FabioImage, OrderedDict

logger = logging.getLogger(__name__)


class MpaImage(FabioImage):
    """
    FabIO image class for Images from multiwire data files (mpa)
    """

    DESCRIPTION = "multiwire data files"

    DEFAULT_EXTENSIONS = ["mpa"]

    def _readheader(self, infile):
        """
        Read and decode the header of an image

        :param infile: Opened python file (can be stringIO or bzipped file)
        """
        # list of header key to keep the order (when writing)
        header_prefix = ''
        tmp_hdr = OrderedDict([("None", OrderedDict())])

        while True:
            line = infile.readline()
            line = line.decode()
            if line.find('=') > -1:
                key, value = line.strip().split('=', 1)
                key = key.strip()
                value = value.strip()
                if header_prefix == '':
                    tmp_hdr["None"][key] = value
                else:
                    tmp_hdr[header_prefix][key] = value
            elif line.startswith('[DATA') or line.startswith('[CDAT'):
                break
            else:
                header_prefix = line.strip().strip('[]')
                tmp_hdr[header_prefix] = {}

        self.header = OrderedDict()
        for key, key_data in tmp_hdr.items():
            key = str(key)
            for subkey, subkey_data in key_data.items():
                subkey = str(subkey)
                if key == 'None':
                    self.header[subkey] = subkey_data
                else:
                    self.header[key + '_' + subkey] = subkey_data

    def read(self, fname, frame=None):
        """
        Try to read image

        :param fname: name of the file
        """

        infile = self._open(fname, 'r')
        self._readheader(infile)

        if ('ADC1_range' not in self.header.keys() or
                'ADC2_range' not in self.header.keys() or
                'mpafmt' not in self.header.keys()):
            logger.error('Error in opening %s: badly formatted mpa header.', fname)
            raise IOError('Error in opening %s: badly formatted mpa header.' % fname)

        dim2 = int(self.header['ADC1_range'])
        dim1 = int(self.header['ADC2_range'])
        self._shape = dim2, dim1

        if self.header['mpafmt'] == 'asc':
            lines = infile.readlines()
        else:
            infile.close()
            infile = self._open(fname, 'rb')
            lines = infile.readlines()

        for i, line in enumerate(lines):
            if line.startswith(b'[CDAT'):
                pos = i
                break

        img = numpy.array(lines[pos + 1:], dtype=float)
        self.data = img.reshape(self._shape)
        self._shape = None

        return self


mpaimage = MpaImage
