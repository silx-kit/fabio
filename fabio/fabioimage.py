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

         and Jon Wright, Jerome Kieffer: ESRF

"""
# get ready for python3
from __future__ import with_statement, print_function, absolute_import, division
import os
import logging
import sys
import tempfile
logger = logging.getLogger("fabioimage")
import numpy
try:
    from PIL import Image
except ImportError:
    logger.warning("PIL is not installed ... trying to do without")
    Image = None
from . import fabioutils, converters

try:
    from .third_party.six import with_metaclass
except ImportError:
    import six
    six_version = tuple(int(i) for i in six.__version__.split() if i.isdigit())
    if six_version < (1, 8):
        for i in ("six", "six.moves"):
            sys.modules.pop(i, None)
        raise ImportError("Old version")
    from six import with_metaclass


try:
    from collections import OrderedDict
except ImportError:
    from .third_party.ordereddict import OrderedDict


class FabioMeta(type):
    """ Metaclass used to register all image classes inheriting from fabioImage
    """
    # we use __init__ rather than __new__ here because we want
    # to modify attributes of the class *after* they have been
    # created
    def __init__(cls, name, bases, dct):
        cls.registry[name.lower()] = cls
        super(FabioMeta, cls).__init__(name, bases, dct)


class FabioImage(with_metaclass(FabioMeta, object)):
    """A common object for images in fable
    
    Contains a numpy array (.data) and dict of meta data (.header)
    """

    _need_a_seek_to_read = False
    _need_a_real_file = False
    registry = OrderedDict()  # list of child classes ...

    @classmethod
    def factory(cls, name):
        """A kind of factory... for image_classes

        @param name: name of the class to instantiate
        @type name: str
        @return: an instance of the class
        @rtype: fabioimage
        """
        name = name.lower()
        obj = None
        if name in cls.registry:
            obj = cls.registry[name]()
        else:
            msg = ("FileType %s is unknown !, "
                   "please check if the filename exists or select one from %s" % (name, cls.registry.keys()))
            logger.error(msg)
            raise RuntimeError(msg)
        return obj

    def __init__(self, data=None, header=None):
        """Set up initial values
        
        @param data: numpy array of values
        @param header: dict or ordereddict with metadata 
        """
        self._classname = None
        self._dim1 = self._dim2 = self._bpp = 0
        self._bytecode = None
        if type(data) in fabioutils.StringTypes:
            raise Exception("fabioimage.__init__ bad argument - " + \
                            "data should be numpy array")
        self.data = self.check_data(data)
        self.pilimage = None
        self.header = self.check_header(header)
        # cache for image statistics
        self.mean = self.maxval = self.stddev = self.minval = None
        # Cache roi
        self.roi = None
        self.area_sum = None
        self.slice = None
        # New for multiframe files
        self.nframes = 1
        self.currentframe = 0
        self.filename = None
        self.filenumber = None

    def get_header_keys(self):
        return list(self.header.keys())

    def set_header_keys(self, value):
        pass

    header_keys = property(get_header_keys, set_header_keys)

    def get_dim1(self):
        "Getter for dim1: data superseeds _dim1"
        if self.data is not None:
            try:
                return self.data.shape[-1]
            except IndexError as err:
                logger.error(err)
                print(self.data)
                return self._dim1
        else:
            return self._dim1

    def set_dim1(self, value):
        "Setter for dim1"
        self._dim1 = value

    dim1 = property(get_dim1, set_dim1)

    def get_dim2(self):
        "Getter for dim2: data superseeds _dim2"
        if self.data is not None:
            try:
                return self.data.shape[-2]
            except IndexError as err:
                logger.error(err)
                print(self.data)
                return self._dim2
        else:
            return self._dim2

    def set_dim2(self, value):
        "Setter for dim2"
        self._dim2 = value

    dim2 = property(get_dim2, set_dim2)

    def get_bpp(self):
        "Getter for bpp: data superseeds _bpp"
        if self.data is not None:
            return numpy.dtype(self.data.dtype).itemsize
        elif self._bytecode is not None:
            return numpy.dtype(self._bytecode).itemsize
        else:
            return self._bpp

    def set_bpp(self, value):
        "Setter for bpp"
        self._bpp = value
    bpp = property(get_bpp, set_bpp)

    def get_bytecode(self):
        "Getter for bpp: data superseeds _bytecode"
        if self.data is not None:
            return self.data.dtype.type
        else:
            return self._bytecode

    def set_bytecode(self, value):
        "Setter for bpp"
        self._bytecode = value
    bytecode = property(get_bytecode, set_bytecode)

    @staticmethod
    def check_header(header=None):
        """
        Empty for fabioimage but may be populated by others classes

        @param header: dict like object
        @return: Ordered dict
        """
        if header is None:
            return OrderedDict()
        else:
            return OrderedDict(header)

    @staticmethod
    def check_data(data=None):
        """
        Empty for fabioimage but may be populated by others classes,
        especially for format accepting only integers

        @param data: array like
        @return: numpy array or None
        """
        if data is None:
            return None
        else:
            return data

    def getclassname(self):
        """
        Retrieves the name of the class
        @return: the name of the class
        """
        if self._classname is None:
            self._classname = str(self.__class__).replace("<class '", "").replace("'>", "").split(".")[-1]
        return self._classname
    classname = property(getclassname)

    def getframe(self, num):
        """ returns the file numbered 'num' in the series as a fabioimage """
        if self.nframes == 1:
            # single image per file
            from .openimage import openimage
            return openimage(fabioutils.jump_filename(self.filename, num))
        raise Exception("getframe out of range")

    def previous(self):
        """ returns the previous file in the series as a fabioimage """
        from .openimage import openimage
        return openimage(fabioutils.previous_filename(self.filename))

    def next(self):
        """ returns the next file in the series as a fabioimage """
        from .openimage import openimage
        return openimage(
            fabioutils.next_filename(self.filename))

    def toPIL16(self, filename=None):
        """
        Convert to Python Imaging Library 16 bit greyscale image

        """
        if not Image:
            raise RuntimeError("PIL is not installed !!! ")
        if filename:
            self.read(filename)
        if self.pilimage is not None:
            return self.pilimage
        # mode map
        size = self.data.shape[:2][::-1]
        typmap = {
                  'float32': "F",
                  'int32': "F;32NS",
                  'uint32': "F;32N",
                  'int16': "F;16NS",
                  'uint16': "F;16N",
                  'int8': "F;8S",
                  'uint8': "F;8"
                 }
        if self.data.dtype.name in typmap:
            mode2 = typmap[self.data.dtype.name]
            mode1 = mode2[0]
        else:
            raise RuntimeError("Unknown numpy type: %s" % (self.data.dtype.type))
        dats = self.data.tostring()
        self.pilimage = Image.frombuffer(mode1, size, dats, "raw", mode2, 0, 1)

        return self.pilimage

    def getheader(self):
        """ returns self.header """
        return self.header

    def getmax(self):
        """ Find max value in self.data, caching for the future """
        if self.maxval is None:
            if self.data is not None:
                self.maxval = self.data.max()
        return self.maxval

    def getmin(self):
        """ Find min value in self.data, caching for the future """
        if self.minval is None:
            if self.data is not None:
                self.minval = self.data.min()
        return self.minval

    def make_slice(self, coords):
        """
        Convert a len(4) set of coords into a len(2)
        tuple (pair) of slice objects
        the latter are immutable, meaning the roi can be cached
        """
        assert len(coords) == 4
        if len(coords) == 4:
            # fabian edfimage preference
            if coords[0] > coords[2]:
                coords[0:3:2] = [coords[2], coords[0]]
            if coords[1] > coords[3]:
                coords[1:4:2] = [coords[3], coords[1]]
            # in fabian: normally coordinates are given as (x,y) whereas
            # a matrix is given as row,col
            # also the (for whichever reason) the image is flipped upside
            # down wrt to the matrix hence these tranformations
            fixme = (self.dim2 - coords[3] - 1,
                     coords[0],
                     self.dim2 - coords[1] - 1,
                     coords[2])
        return (slice(int(fixme[0]), int(fixme[2]) + 1),
                slice(int(fixme[1]), int(fixme[3]) + 1))

    def integrate_area(self, coords):
        """
        Sums up a region of interest
        if len(coords) == 4 -> convert coords to slices
        if len(coords) == 2 -> use as slices
        floor -> ? removed as unused in the function.
        """
        if self.data is None:
            # This should return NAN, not zero ?
            return 0
        if len(coords) == 4:
            sli = self.make_slice(coords)
        elif len(coords) == 2 and isinstance(coords[0], slice) and \
                        isinstance(coords[1], slice):
            sli = coords

        if sli == self.slice and self.area_sum is not None:
            pass
        elif sli == self.slice and self.roi is not None:
            self.area_sum = self.roi.sum(dtype=numpy.float)
        else:
            self.slice = sli
            self.roi = self.data[self.slice]
            self.area_sum = self.roi.sum(dtype=numpy.float)
        return self.area_sum

    def getmean(self):
        """ return the mean """
        if self.mean is None:
            self.mean = self.data.mean(dtype=numpy.double)
        return self.mean

    def getstddev(self):
        """ return the standard deviation """
        if self.stddev is None:
            self.stddev = self.data.std(dtype=numpy.double)
        return self.stddev

    def add(self, other):
        """
        Add another Image - warning, does not clip to 16 bit images by default
        """
        if not hasattr(other, 'data'):
            logger.warning('edfimage.add() called with something that '
                           'does not have a data field')
        assert self.data.shape == other.data.shape, 'incompatible images - Do they have the same size?'
        self.data = self.data + other.data
        self.resetvals()

    def resetvals(self):
        """ Reset cache - call on changing data """
        self.mean = self.stddev = self.maxval = self.minval = None
        self.roi = self.slice = self.area_sum = None

    def rebin(self, x_rebin_fact, y_rebin_fact, keep_I=True):
        """
        Rebin the data and adjust dims
        @param x_rebin_fact: x binning factor
        @param y_rebin_fact: y binning factor
        @param keep_I: shall the signal increase ?
        @type x_rebin_fact: int
        @type y_rebin_fact: int
        @type keep_I: boolean


        """
        if self.data is None:
            raise Exception('Please read in the file you wish to rebin first')

        if (self.dim1 % x_rebin_fact != 0) or (self.dim2 % y_rebin_fact != 0):
            raise RuntimeError('image size is not divisible by rebin factor - '
                               'skipping rebin')
        else:
            dataIn = self.data.astype("float64")
            shapeIn = self.data.shape
            shapeOut = (shapeIn[0] // y_rebin_fact, shapeIn[1] // x_rebin_fact)
            binsize = y_rebin_fact * x_rebin_fact
            if binsize < 50:  # method faster for small binning (4x4)
                out = numpy.zeros(shapeOut, dtype="float64")
                for j in range(x_rebin_fact):
                    for i in range(y_rebin_fact):
                        out += dataIn[i::y_rebin_fact, j::x_rebin_fact]
            else:  # method faster for large binning (8x8)
                temp = self.data.astype("float64")
                temp.shape = (shapeOut[0], y_rebin_fact, shapeOut[1], x_rebin_fact)
                out = temp.sum(axis=3).sum(axis=1)
        self.resetvals()
        if keep_I:
            self.data = (out / (y_rebin_fact * x_rebin_fact)).astype(self.data.dtype)
        else:
            self.data = out.astype(self.data.dtype)

        self.dim1 = self.dim1 / x_rebin_fact
        self.dim2 = self.dim2 / y_rebin_fact

        # update header
        self.update_header()

    def write(self, fname):
        """
        To be overwritten - write the file
        """
        raise Exception("Class has not implemented readheader method yet")

    def save(self, fname):
        'wrapper for write'
        self.write(fname)

    def readheader(self, filename):
        """
        Call the _readheader function...
        """
        # Override the needs asserting that all headers can be read via python modules
        save_state = self._need_a_real_file, self._need_a_seek_to_read
        self._need_a_real_file, self._need_a_seek_to_read = False, False
        fin = self._open(filename)
        self._readheader(fin)
        fin.close()
        self._need_a_real_file, self._need_a_seek_to_read = save_state

    def _readheader(self, fik_obj):
        """
        Must be overridden in classes
        """
        raise Exception("Class has not implemented _readheader method yet")

    def update_header(self, **kwds):
        """
        update the header entries
        by default pass in a dict of key, values.
        """
        self.header.update(kwds)

    def read(self, filename, frame=None):
        """
        To be overridden - fill in self.header and self.data
        """
        raise Exception("Class has not implemented read method yet")
#        return self

    def load(self, *arg, **kwarg):
        "Wrapper for read"
        return self.read(*arg, **kwarg)

    def readROI(self, filename, frame=None, coords=None):
        """
        Method reading Region of Interest.
        This implementation is the trivial one, just doing read and crop
        """
        self.read(filename, frame)
        if len(coords) == 4:
            self.slice = self.make_slice(coords)
        elif len(coords) == 2 and isinstance(coords[0], slice) and \
             isinstance(coords[1], slice):
            self.slice = coords
        else:
            logger.warning('readROI: Unable to understand Region Of Interest: got %s', coords)
        self.roi = self.data[self.slice]
        return self.roi

    def _open(self, fname, mode="rb"):
        """
        Try to handle compressed files, streams, shared memory etc
        Return an object which can be used for "read" and "write"
        ... FIXME - what about seek ?
        """

        if hasattr(fname, "read") and hasattr(fname, "write"):
            # It is already something we can use
            if "name" in dir(fname):
                self.filename = fname.name
            else:
                self.filename = "stream"
                try:
                    setattr(fname, "name", self.filename)
                except AttributeError:
                    # cStringIO
                    logger.warning("Unable to set filename attribute to stream (cStringIO?) of type %s" % type(fname))
            return fname

        fileObject = None
        self.filename = fname
        self.filenumber = fabioutils.extract_filenumber(fname)

        if isinstance(fname, fabioutils.StringTypes):
            comp_type = os.path.splitext(fname)[-1]
            if comp_type == ".gz":
                fileObject = self._compressed_stream(fname,
                                                     fabioutils.COMPRESSORS['.gz'],
                                                     fabioutils.GzipFile,
                                                     mode)
            elif comp_type == '.bz2':
                fileObject = self._compressed_stream(fname,
                                                     fabioutils.COMPRESSORS['.bz2'],
                                                     fabioutils.BZ2File,
                                                     mode)
            #
            # Here we return the file even though it may be bzipped or gzipped
            # but named incorrectly...
            #
            # FIXME - should we fix that or complain about the daft naming?
            else:
                fileObject = fabioutils.File(fname, mode)
            if "name" not in dir(fileObject):
                fileObject.name = fname

        return fileObject

    def _compressed_stream(self,
                           fname,
                           system_uncompress,
                           python_uncompress,
                           mode='rb'):
        """
        Try to transparently handle gzip / bzip2 without always getting python
        performance
        """
        # assert that python modules are always OK based on performance benchmark
        # Try to fix the way we are using them?
        fobj = None
        if self._need_a_real_file and mode[0] == "r":
            fo = python_uncompress(fname, mode)
            # problem when not administrator under certain flavors of windows
            tmpfd, tmpfn = tempfile.mkstemp()
            os.close(tmpfd)
            fobj = fabioutils.File(tmpfn, "w+b", temporary=True)
            fobj.write(fo.read())
            fo.close()
            fobj.seek(0)
        elif self._need_a_seek_to_read and mode[0] == "r":
            fo = python_uncompress(fname, mode)
            fobj = fabioutils.BytesIO(fo.read(), fname, mode)
        else:
            fobj = python_uncompress(fname, mode)
        return fobj

    def convert(self, dest):
        """
        Convert a fabioimage object into another fabioimage object (with possible conversions)
        @param dest: destination type "EDF", "edfimage" or the class itself
        @return: instance of the new class
        """
        other = None
        if type(dest) in fabioutils.StringTypes:
            dest = dest.lower()
            if dest.endswith("image"):
                dest = dest[:-5]
            if dest + "image" in self.registry:
                other = self.factory(dest + "image")
            # load modules which could be suitable:
            for pref in fabioutils.FILETYPES.get(dest, []):
                try:
                    __import__(".%simage" % pref)
                    other = self.factory(pref + "image")
                except:
                    pass
                else:
                    continue

        elif isinstance(dest, self.__class__):
            other = dest.__class__()
        elif ("__new__" in dir(dest)) and isinstance(dest(), fabioimage):
            other = dest()
        else:
            logger.error("Unrecognized destination format: %s " % dest)
            return self
        other.data = converters.convert_data(self.classname, other.classname, self.data)
        other.header = converters.convert_header(self.classname, other.classname, self.header)
        return other

    def __iter__(self):
        current_image = self
        while True:
            yield current_image
            try:
                current_image = current_image.next()
            except IOError:
                raise StopIteration


fabioimage = FabioImage
