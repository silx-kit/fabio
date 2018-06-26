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
# THE SOFTWARE.
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

__authors__ = ["Henning O. Sorensen", "Erik Knudsen", "Jon Wright", "Jérôme Kieffer"]
__contact__ = "jerome.kieffer@esrf.fr"
__license__ = "MIT"
__copyright__ = "ESRF"
__date__ = "11/06/2018"

import os
import logging
import sys
import tempfile
logger = logging.getLogger(__name__)
import numpy
from . import fabioutils, converters
from .fabioutils import six, OrderedDict
from .utils import pilutils


class FabioMeta(type):
    """ Metaclass used to register all image classes inheriting from fabioImage
    """
    # we use __init__ rather than __new__ here because we want
    # to modify attributes of the class *after* they have been
    # created
    def __init__(cls, name, bases, dct):
        if cls.codec_name() != "fabioimage":
            cls.registry[cls.codec_name()] = cls
        super(FabioMeta, cls).__init__(name, bases, dct)

    @property
    def DEFAULT_EXTENTIONS(self):
        """
        Compatibility with the wrong typo.

        .. note:: Will be marked as deprecated for the following version 0.7.
        """
        return self.DEFAULT_EXTENSIONS

    @DEFAULT_EXTENTIONS.setter
    def DEFAULT_EXTENTIONS(self, extensions):
        """
        Compatibility with the wrong typo.

        .. note:: Will be marked as deprecated for the following version 0.7.
        """
        self.DEFAULT_EXTENSIONS = extensions


class FabioImage(six.with_metaclass(FabioMeta, object)):
    """A common object for images in fable

    Contains a numpy array (.data) and dict of meta data (.header)
    """

    _need_a_seek_to_read = False
    _need_a_real_file = False
    registry = OrderedDict()  # list of child classes ...

    RESERVED_HEADER_KEYS = []
    # List of header keys which are reserved by the file format

    @classmethod
    def factory(cls, name):
        """A kind of factory... for image_classes

        :param str name: name of the class to instantiate
        :return: an instance of the class
        :rtype: fabio.fabioimage.FabioImage
        """
        name = name.lower()
        obj = None
        if name in cls.registry:
            obj = cls.registry[name]()
        else:
            msg = ("FileType %s is unknown !, "
                   "please check if the filename exists or select one from %s" % (name, cls.registry.keys()))
            logger.debug(msg)
            raise RuntimeError(msg)
        return obj

    @classmethod
    def codec_name(cls):
        """Returns the internal name of the codec"""
        return cls.__name__.lower()

    def __init__(self, data=None, header=None):
        """Set up initial values

        :param data: numpy array of values
        :param header: dict or ordereddict with metadata
        """
        self._classname = None
        self._dim1 = self._dim2 = self._bpp = 0
        self._bytecode = None
        self._file = None
        if type(data) in fabioutils.StringTypes:
            raise Exception("fabioimage.__init__ bad argument - " +
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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, tb):
        # TODO: inspace type, value and traceback
        self.close()

    def close(self):
        if self._file is not None and not self._file.closed:
            self._file.close()
        self._file = None

    def __copy__(self):
        other = self.__class__(data=self.data, header=self.header)
        if self.nframes > 1:
            logger.warning("Only copying current frame")
        other.filename = self.filename
        return other

    @property
    def incomplete_file(self):
        """Returns true if the readed file is not complete.

        :rtype: bool
        """
        return False

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
                logger.debug(self.data)
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
                logger.debug(self.data)
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

        :param header: dict like object
        :return: Ordered dict
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

        :param data: array like
        :return: numpy array or None
        """
        if data is None:
            return None
        else:
            return data

    def getclassname(self):
        """
        Retrieves the name of the class
        :return: the name of the class
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
        """Returns the next file in the series as a fabioimage

        :raise IOError: When there is no next file in the series.
        """
        from .openimage import openimage
        return openimage(
            fabioutils.next_filename(self.filename))

    def toPIL16(self, filename=None):
        """
        Convert to Python Imaging Library 16 bit greyscale image
        """
        if filename:
            self.read(filename)
        if self.pilimage is None:
            # Create and cache the result
            self.pilimage = pilutils.create_pil_16(self.data)
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
        Accumulate another fabioimage into  the first image.

        Warning, does not clip to 16 bit images by default

        :param FabioImage other: Another image to accumulate.
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
        :param int x_rebin_fact: x binning factor
        :param int y_rebin_fact: y binning factor
        :param bool keep_I: shall the signal increase ?
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
        if isinstance(fname, fabioutils.PathTypes):
            if not isinstance(fname, fabioutils.StringTypes):
                fname = str(fname)
        module = sys.modules[self.__class__.__module__]
        raise NotImplementedError("Writing %s format is not implemented" % module.__name__)

    def save(self, fname):
        'wrapper for write'
        self.write(fname)

    def readheader(self, filename):
        """
        Call the _readheader function...
        """
        # Override the needs asserting that all headers can be read via python modules
        if isinstance(filename, fabioutils.PathTypes):
            if not isinstance(filename, fabioutils.StringTypes):
                filename = str(filename)
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
        if isinstance(filename, fabioutils.PathTypes):
            if not isinstance(filename, fabioutils.StringTypes):
                filename = str(filename)
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

        if isinstance(fname, fabioutils.PathTypes):
            if not isinstance(fname, fabioutils.StringTypes):
                fname = str(fname)
        else:
            raise TypeError("Unsupported type of fname (found %s)" % type(fname))

        fileObject = None
        self.filename = fname
        self.filenumber = fabioutils.extract_filenumber(fname)

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
        self._file = fileObject

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
        :param dest: destination type "EDF", "edfimage" or the class itself
        :return: instance of the new class
        """
        other = None
        if type(dest) in fabioutils.StringTypes:
            dest = dest.lower()
            if dest.endswith("image"):
                dest = dest[:-5]
            if dest + "image" in self.registry:
                other = self.factory(dest + "image")
            else:
                # load modules which could be suitable:
                from . import fabioformats
                for class_ in fabioformats.get_classes_from_extension(dest):
                    try:
                        other = class_()
                    except:
                        pass

        elif isinstance(dest, FabioImage):
            other = dest.__class__()
        elif ("__new__" in dir(dest)) and isinstance(dest(), FabioImage):
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
