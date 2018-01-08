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

Authors:
........
* Henning O. Sorensen & Erik Knudsen:
  Center for Fundamental Research: Metal Structures in Four Dimensions;
  Risoe National Laboratory;
  Frederiksborgvej 399;
  DK-4000 Roskilde;
  email:erik.knudsen@risoe.dk
* Jon Wright:
  European Synchrotron Radiation Facility;
  Grenoble (France)

"""
# Get ready for python3:
from __future__ import with_statement, print_function


# Base this on the tifimage (as Pilatus is tiff with a
# tiff header

from .tifimage import TifImage


class PilatusImage(TifImage):
    """ Read in Pilatus format, also
        pilatus images, including header info """

    DESCRIPTION = "Pilatus file format based on Tiff"

    DEFAULT_EXTENSIONS = ["tif", "tiff"]

    def _readheader(self, infile):
        """
        Parser based approach
        Gets all entries
        """

        self.header = self.check_header()

#        infile = open(infile)
        hstr = infile.read(4096)
        # well not very pretty - but seems to find start of
        # header information
        if (hstr.find(b'# ') == -1):
            return self.header

        hstr = hstr[hstr.index(b'# '):]
        hstr = hstr[:hstr.index(b'\x00')]
        hstr = hstr.split(b'#')
        go_on = True
        while go_on:
            try:
                hstr.remove(b'')
            except Exception:
                go_on = False

        for line in hstr:
            line = line[1:line.index(b'\r\n')]
            if line.find(b':') > -1:
                dump = line.split(b':')
                self.header[dump[0]] = dump[1]
            elif line.find(b'=') > -1:
                dump = line.split(b'=')
                self.header[dump[0]] = dump[1]
            elif line.find(b' ') > -1:
                i = line.find(b' ')
                self.header[line[:i]] = line[i:]
            elif line.find(b',') > -1:
                dump = line.split(b',')
                self.header[dump[0]] = dump[1]

        return self.header

    def _read(self, fname):
        """
        inherited from tifimage
        ... a Pilatus image *is a* tif image
        just with a header
        """
        return TifImage.read(self, fname)


pilatusimage = PilatusImage
