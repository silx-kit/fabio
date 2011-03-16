#!/usr/bin/env python
"""
Authors: Henning O. Sorensen & Erik Knudsen
         Center for Fundamental Research: Metal Structures in Four Dimensions
         Risoe National Laboratory
         Frederiksborgvej 399
         DK-4000 Roskilde
         email:erik.knudsen@risoe.dk
         
         and Jon Wright, ESRF
"""
#import numpy

class fabiodata(object):
    """
    A common class for dataIO in fable
    Contains a 2d numpy array for keeping data, and two lists (clabels and rlabels)
    containing labels for columns and rows respectively
    """

    def __init__(self, data=None, clabels=None, rlabels=None, fname=None):
        """
        set up initial values
        """
        if type(data) == type("string"):
                raise Exception("fabioimage.__init__ bad argument - " + \
                                "data should be numpy array")
        self.data = data
        if (self.data):
            self.dims = self.data.shape
        self.clabels = clabels
        self.rlabels = rlabels
        if (fname):
            self.read(fname)

    def read(self, fname=None):
        """
        To be overridden by format specific subclasses
        """
        raise Exception("Class has not implemented read method yet")

#import stuff from Jon's columnfile things


class columnfile (fabiodata):

    def read(self, fname):
        import cf_io
        try:
            infile = open(fname, 'rb')
        except:
            raise Exception("columnfile: file" + str(fname) + "not found.")
        try:
            (self.data, self.clabels) = cf_io.read(infile)
        except:
            raise Exception("columnfile: read error, file " + str(fname) + " possibly corrupt")
        self.dims = self.data.shape
        infile.close()


