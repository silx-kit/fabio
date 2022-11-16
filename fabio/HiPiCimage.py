#!/usr/bin/env python
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

"""
Authors: Henning O. Sorensen & Erik Knudsen
         Center for Fundamental Research: Metal Structures in Four Dimensions
         Risoe National Laboratory
         Frederiksborgvej 399
         DK-4000 Roskilde
         email:erik.knudsen@risoe.dk

        + Jon Wright, ESRF

Information about the file format from Masakatzu Kobayashi is highly appreciated
"""

import numpy
import logging
logger = logging.getLogger(__name__)
from .fabioimage import FabioImage


class HipicImage(FabioImage):
    """ Read HiPic images e.g. collected with a Hamamatsu CCD camera"""

    DESCRIPTION = "HiPic file format from Hamamatsu CCD cameras"

    DEFAULT_EXTENSIONS = ["img"]

    def _readheader(self, infile):
        """
        Read in a header from an already open file

        """
        Image_tag = infile.read(2).decode()
        Comment_len = numpy.frombuffer(infile.read(2), numpy.uint16)
        Dim_1 = numpy.frombuffer(infile.read(2), numpy.uint16)[0]
        Dim_2 = numpy.frombuffer(infile.read(2), numpy.uint16)[0]
        Dim_1_offset = numpy.frombuffer(infile.read(2), numpy.uint16)[0]
        Dim_2_offset = numpy.frombuffer(infile.read(2), numpy.uint16)[0]
        _HeaderType = numpy.frombuffer(infile.read(2), numpy.uint16)[0]
        _Dump = infile.read(50)
        Comment = infile.read(Comment_len[0])
        Comment = Comment.decode()
        self.header['Image_tag'] = Image_tag
        self.header['Dim_1'] = Dim_1
        self.header['Dim_2'] = Dim_2
        self.header['Dim_1_offset'] = Dim_1_offset
        self.header['Dim_2_offset'] = Dim_2_offset
        # self.header['Comment'] = Comment
        if Image_tag != 'IM':
            # This does not look like an HiPic file
            logger.warning("No opening. Corrupt header of HiPic file %s",
                           str(infile.name))
        Comment_split = Comment[:Comment.find('\x00')].split('\r\n')

        for topcomment in Comment_split:
            topsplit = topcomment.split(',')
            for line in topsplit:
                if '=' in line:
                    key, val = line.split('=', 1)
                    # Users cannot type in significant whitespace
                    key = key.rstrip().lstrip()
                    self.header_keys.append(key)
                    self.header[key] = val.lstrip().rstrip()
                    self.header[key] = val.lstrip('"').rstrip('"')

    def read(self, fname, frame=None):
        """
        Read in header into self.header and
            the data   into self.data
        """
        self.header = self.check_header()
        self.resetvals()
        infile = self._open(fname, "rb")
        self._readheader(infile)
        # Compute image size
        try:
            dim1 = int(self.header['Dim_1'])
            dim2 = int(self.header['Dim_2'])
            self._shape = dim2, dim1
        except (ValueError, KeyError):
            raise IOError("HiPic file %s is corrupted, cannot read it" % str(fname))
        dtype = numpy.dtype(numpy.uint16)
        self._dtype = dtype

        # Read image data
        block = infile.read(dim1 * dim2 * dtype.itemsize)
        infile.close()

        # now read the data into the array
        try:
            self.data = numpy.frombuffer(block, dtype).copy().reshape((dim2, dim1))
        except Exception:
            logger.debug("%s %s %s %s %s", len(block), dtype, self.bpp, dim2, dim1)
            logger.debug("Backtrace", exc_info=True)
            raise IOError('Size spec in HiPic-header does not match size of image data field')
        self._dtype = None
        self._shape = None


        #### The case below is not true for data collected at 
        #### BL47XU/BL20XU/BL20B at SPring-8 - here the data is saved as 
        #### 16 bit - so values above 4095 should be negative.
        #### Therefore I have now commented it out.
        
        # # Sometimes these files are not saved as 12 bit,
        # # But as 16 bit after bg subtraction - which results
        # # negative values saved as 16bit. Therefore values higher
        # # 4095 is really negative values
        # if self.data.max() > 4095:
        #     gt12bit = self.data > 4095
        #     self.data = self.data - gt12bit * (2 ** 16 - 1)
        return self


HiPiCimage = HipicImage
