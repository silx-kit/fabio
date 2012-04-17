#!/usr/bin/env python
#coding: utf8
"""

Authors: Henning O. Sorensen & Erik Knudsen
         Center for Fundamental Research: Metal Structures in Four Dimensions
         Risoe National Laboratory
         Frederiksborgvej 399
         DK-4000 Roskilde
         email:henning.sorensen@risoe.dk

         + (mods for fabio) Jon Wright, ESRF
marccdimage can read MarCCD and MarMosaic images including header info.

JPW : Use a parser in case of typos (sorry?)

"""


# Base this on the tifimage (as Pilatus is tiff with a 
# tiff header 

from fabio.tifimage import tifimage


class pilatusimage(tifimage):
    """ Read in Pilatus format, also 
        pilatus images, including header info """


    def _readheader(self, infile):
        """
        Parser based approach
        Gets all entries
        """

        self.header = {}

#        infile = open(infile)
        hstr = infile.read(4096)
        # well not very pretty - but seems to find start of 
        # header information
        if (hstr.find('# ') == -1):
            return self.header

        hstr = hstr[hstr.index('# '):]
        hstr = hstr[:hstr.index('\x00')]
        hstr = hstr.split('#')
        go_on = True
        while go_on:
            try:
                hstr.remove('')
            except Exception:
                go_on = False

        for line in hstr:
            line = line[1:line.index('\r\n')]
            if line.find(':') > -1:
                dump = line.split(':')
                self.header[dump[0]] = dump[1]
            elif line.find('=') > -1:
                dump = line.split('=')
                self.header[dump[0]] = dump[1]
            elif line.find(' ') > -1:
                i = line.find(' ')
                self.header[line[:i]] = line[i:]
            elif line.find(',') > -1:
                dump = line.split(',')
                self.header[dump[0]] = dump[1]

        return self.header



    def _read(self, fname):
        """
        inherited from tifimage
        ... a Pilatus image *is a* tif image
        just with a header
        """
        return tifimage.read(self, fname)
