#!/usr/bin/env python# coding: utf-8
#
#    Project: X-ray image reader
#             https://github.com/silx-kit/fabio
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

        + Jon Wright, ESRF

Information about the file format from Masakatzu Kobayashi is highly appreciated
"""
# Get ready for python3:
from __future__ import with_statement, print_function

import numpy, logging
logger = logging.getLogger("HipiciImage")
from .fabioimage import FabioImage


class HipicImage(FabioImage):
    """ Read HiPic images e.g. collected with a Hamamatsu CCD camera"""


    def _readheader(self, infile):
        """
        Read in a header from an already open file

        """
        Image_tag = infile.read(2)
        Comment_len = numpy.fromstring(infile.read(2), numpy.uint16)
        Dim_1 = numpy.fromstring(infile.read(2), numpy.uint16)[0]
        Dim_2 = numpy.fromstring(infile.read(2), numpy.uint16)[0]
        Dim_1_offset = numpy.fromstring(infile.read(2), numpy.uint16)[0]
        Dim_2_offset = numpy.fromstring(infile.read(2), numpy.uint16)[0]
        HeaderType = numpy.fromstring(infile.read(2), numpy.uint16)[0]
        Dump = infile.read(50)
        Comment = infile.read(Comment_len)
        self.header['Image_tag'] = Image_tag
        self.header['Dim_1'] = Dim_1
        self.header['Dim_2'] = Dim_2
        self.header['Dim_1_offset'] = Dim_1_offset
        self.header['Dim_2_offset'] = Dim_2_offset
        # self.header['Comment'] = Comment
        if Image_tag != 'IM' :
            # This does not look like an HiPic file
            logging.warning("no opening.  Corrupt header of HiPic file " + \
                            str(infile.name))
        Comment_split = Comment[:Comment.find('\x00')].split('\r\n')

        for topcomment in Comment_split:
            topsplit = topcomment.split(',')
            for line in topsplit:
                if '=' in line:
                    key, val = line.split('=' , 1)
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
            self.dim1 = int(self.header['Dim_1'])
            self.dim2 = int(self.header['Dim_2'])
        except:
            raise Exception("HiPic file", str(fname) + \
                                "is corrupt, cannot read it")
        bytecode = numpy.uint16
        self.bpp = len(numpy.array(0, bytecode).tostring())

        # Read image data
        block = infile.read(self.dim1 * self.dim2 * self.bpp)
        infile.close()

        # now read the data into the array
        try:
            self.data = numpy.reshape(
                numpy.fromstring(block, bytecode),
                [self.dim2, self.dim1])
        except:
            print(len(block), bytecode, self.bpp, self.dim2, self.dim1)
            raise IOError(
              'Size spec in HiPic-header does not match size of image data field')
        self.bytecode = self.data.dtype.type

        # Sometimes these files are not saved as 12 bit,
        # But as 16 bit after bg subtraction - which results
        # negative values saved as 16bit. Therefore values higher
        # 4095 is really negative values
        if self.data.max() > 4095:
            gt12bit = self.data > 4095
            self.data = self.data - gt12bit * (2 ** 16 - 1)

        # ensure the PIL image is reset
        self.pilimage = None
        return self


HiPiCimage = HipicImage
