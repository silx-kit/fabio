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

__authors__ = ["Henning O. Sorensen", "Erik Knudsen", "Jon Wright", "Jérôme Kieffer"]
__contact__ = "jerome.kieffer@esrf.fr"
__license__ = "MIT"
__copyright__ = "ESRF"
__date__ = "04/05/2021"

import os
import logging
import sys
import tempfile
import weakref
logger = logging.getLogger(__name__)
import numpy
from . import fabioutils, converters
from .fabioutils import OrderedDict
from .utils import pilutils
from .utils import deprecation


class _FabioArray(object):
    """"Abstract class providing array API used by :class:`FabioImage` and
    :class:`FabioFrame`."""

    @property
    @deprecation.deprecated(reason="Prefer using 'shape[-1]' instead of 'dim1'", deprecated_since="0.10.0beta")
    def dim1(self):
        return self.shape[-1]

    @property
    @deprecation.deprecated(reason="Prefer using 'shape[-2]' instead of 'dim2'", deprecated_since="0.10.0beta")
    def dim2(self):
        return self.shape[-2]

    @dim1.setter
    @deprecation.deprecated(reason="dim1 should not be updated", deprecated_since="0.10.0beta")
    def dim1(self, value):
        self.__set_dim1(value)

    @dim2.setter
    @deprecation.deprecated(reason="dim2 should not be updated", deprecated_since="0.10.0beta")
    def dim2(self, value):
        self.__set_dim2(value)

    @property
    @deprecation.deprecated(reason="Prefer using 'shape[-3]' instead of 'dim3'", deprecated_since="0.10.0beta")
    def dim3(self):
        if len(self.shape) < 3:
            raise AttributeError("No attribye dim3")
        return self.shape[-3]

    @property
    @deprecation.deprecated(reason="Prefer using 'shape' instead of 'dims' (the content in reverse order)", deprecated_since="0.10.0beta")
    def dims(self):
        return list(reversed(self.shape))

    @deprecation.deprecated(reason="Prefer using 'shape[-1]' instead of 'get_dim1'", deprecated_since="0.10.0beta")
    def get_dim1(self):
        return self.shape[-1]

    @deprecation.deprecated(reason="Prefer using 'shape[-2]' instead of 'get_dim2'", deprecated_since="0.10.0beta")
    def get_dim2(self):
        return self.shape[-2]

    @deprecation.deprecated(reason="dim1 should not be updated", deprecated_since="0.10.0beta")
    def set_dim1(self, value):
        self.__set_dim1(value)

    @deprecation.deprecated(reason="dim2 should not be updated", deprecated_since="0.10.0beta")
    def set_dim2(self, value):
        self.__set_dim2(value)

    def __set_dim1(self, value):
        self.data.shape = self.data.shape[:-2] + (-1, value)

    def __set_dim2(self, value):
        self.data.shape = self.data.shape[:-2] + (value, -1)

    def resetvals(self):
        """ Reset cache - call on changing data """
        self.mean = None
        self.stddev = None
        self.maxval = None
        self.minval = None
        self.roi = None
        self.slice = None
        self.area_sum = None

    @deprecation.deprecated(reason="Not maintained", replacement="fabio.utils.pilutils.create_pil_16", since_version="0.9")
    def toPIL16(self, filename=None):
        """
        Convert the image to Python Imaging Library 16-bits greyscale image.
        """
        if filename:
            self.read(filename)
        return pilutils.create_pil_16(self.data)

    @property
    @deprecation.deprecated(reason="Not maintained", replacement="fabio.utils.pilutils.create_pil_16", since_version="0.9")
    def pilimage(self):
        """
        Convert the image to Python Imaging Library 16-bits greyscale image.
        """
        return self.toPIL16()

    @pilimage.setter
    @deprecation.deprecated(reason="Setting pilimage not supported. This attrbute is not cached anymore", deprecated_since="0.10.0beta")
    def pilimage(self, value):
        if value is not None:
            raise ValueError("Setting pilimage attribute is not supported")

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
            dim2, dim1 = self.data.shape
            # FIXME: This code is just not working dim2 is used in place of dim1
            fixme = (dim2 - coords[3] - 1,
                     coords[0],
                     dim2 - coords[1] - 1,
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
            self.area_sum = self.roi.sum(dtype=numpy.float64)
        else:
            self.slice = sli
            self.roi = self.data[self.slice]
            self.area_sum = self.roi.sum(dtype=numpy.float64)
        return self.area_sum

    def getmean(self):
        """ return the mean """
        if self.mean is None:
            self.mean = self.data.mean(dtype=numpy.float64)
        return self.mean

    def getstddev(self):
        """ return the standard deviation """
        if self.stddev is None:
            self.stddev = self.data.std(dtype=numpy.float64)
        return self.stddev

    @property
    def header_keys(self):
        return list(self.header.keys())

    def get_header_keys(self):
        return self.header_keys()

    @property
    def bpp(self):
        "Getter for bpp: data superseeds _bpp"
        if self.data is not None:
            return self.data.dtype.itemsize
        return self.dtype.itemsize

    def get_bpp(self):
        return self.bpp

    @property
    def bytecode(self):
        "Getter for bpp: data superseeds _bytecode"
        if self.data is not None:
            return self.data.dtype.type
        return self.dtype.type

    def get_bytecode(self):
        return self.bytecode

    @deprecation.deprecated(reason="Prefer using 'bytecode' instead of 'getByteCode'", deprecated_since="0.10.0beta")
    def getByteCode(self):
        return self.bytecode


class FabioFrame(_FabioArray):
    """Identify a frame"""

    def __init__(self, data=None, header=None):
        super(FabioFrame, self).__init__()
        self.data = data
        self._header = header
        self._shape = None
        self._dtype = None
        self._file_container = None
        self._file_index = None
        self._container = None
        self._index = None

    def _set_file_container(self, fabio_image, index):
        """
        Set the file container of this frame

        :param FabioImage fabio_image: The fabio image containing this frame
        :param int index: Index of this frame in the file container (starting
            from 0)
        """
        self._file_container = weakref.ref(fabio_image)
        self._file_index = index

    def _set_container(self, fabio_image, index):
        """
        Set the container of this frame

        :param FabioImage fabio_image: The fabio image containing this frame
        :param int index: Index of this frame in the file container (starting
            from 0)
        """
        self._container = weakref.ref(fabio_image)
        self._index = index

    @property
    def container(self):
        """Returns the container providing this frame.

        This FabioImage is stored as a weakref. If a reference to the file is
        not stored by user of the lib, this link is lost.

        :rtype: FabioImage
        """
        ref = self._container
        if ref is None:
            return None
        ref = ref()
        if ref is None:
            self._container = None
        return ref

    @property
    def index(self):
        """Returns the index of this frame in in it's container.

        :rtype: int
        """
        return self._index

    @property
    def file_container(self):
        """Returns the file container providing this frame.

        This FabioImage is stored as a weakref. If a reference to the file is
        not stored by user of the lib, this link is lost.

        :rtype: FabioImage
        """
        ref = self._file_container
        if ref is None:
            return None
        ref = ref()
        if ref is None:
            self._file_container = None
        return ref

    @property
    def file_index(self):
        """Returns the index of this frame in in it's file container.

        :rtype: int
        """
        return self._file_index

    @property
    def header(self):
        """Default header exposed by fabio

        :rtype: dict
        """
        return self._header

    @header.setter
    def header(self, header):
        """Set the default header exposed by fabio

        :param dict header: The new header
        """
        self._header = header

    @property
    def shape(self):
        if self._shape is not None:
            return self._shape
        return self.data.shape

    @shape.setter
    def shape(self, shape):
        if self.data is not None:
            self.data.shape = shape
            self._shape = None
        else:
            self._shape = shape

    @property
    def dtype(self):
        if self._dtype is not None:
            return self._dtype
        return self.data.dtype

    def next(self):
        """Returns the next frame from it's file container.

        :rtype: FabioFrame
        """
        container = self.file_container
        return container.get_frame(self.file_index + 1)


class FabioImage(_FabioArray):
    """A common object for images in fable

    Contains a numpy array (.data) and dict of meta data (.header)
    """

    _need_a_seek_to_read = False
    _need_a_real_file = False

    RESERVED_HEADER_KEYS = []
    # List of header keys which are reserved by the file format

    @classmethod
    @deprecation.deprecated
    def factory(cls, name):
        """A kind of factory... for image_classes

        :param str name: name of the class to instantiate
        :return: an instance of the class
        :rtype: fabio.fabioimage.FabioImage
        """
        from . import fabioformats
        return fabioformats.factory(name)

    @classmethod
    def codec_name(cls):
        """Returns the internal name of the codec"""
        return cls.__name__.lower()

    def __init__(self, data=None, header=None):
        """Set up initial values

        :param data: numpy array of values
        :param header: dict or ordereddict with metadata
        """
        super(FabioImage, self).__init__()
        self._classname = None
        self._shape = None
        self._dtype = None
        self._file = None
        if type(data) in fabioutils.StringTypes:
            raise TypeError("Data should be numpy array")
        self._nframes = 1
        self.currentframe = 0
        self.data = self.check_data(data)
        self.header = self.check_header(header)
        # cache for image statistics
        self.filename = None
        self.filenumber = None

        self.resetvals()

    @property
    def nframes(self):
        """Returns the number of frames contained in this file

        :rtype: int
        """
        return self._nframes

    def get_frame(self, num):
        """Returns a frame from the this fabio image.

        :param int num: Number of frames (0 is the first frame)
        :rtype: FabioFrame
        :raises IndexError: If the frame number is out of the available range.
        """
        return self._get_frame(num)

    def _get_frame(self, num):
        """Returns a frame from the this fabio image.

        This method have to be reimplemented to provide multi frames using a
        a custom class.

        :param int num: Number of frames (0 is the first frame)
        :rtype: FabioFrame
        :raises IndexError: If the frame number is out of the available range.
        """
        if self.nframes == 1 and num == 0:
            frame = FabioFrame(self.data, self.header)
        else:
            if not (0 <= num < self.nframes):
                raise IndexError("Frame number out of range (requested %d, but found %d)" % (num, self.nframes))

            # Try to use the old getframe API to avoid to implement many
            # things on mostly unused formats.
            # This could be avoided by inheriting `_get_frame` on specific
            # formats.

            image = self.getframe(num)
            # Usually it is not a FabioFrame
            if isinstance(image, FabioFrame):
                frame = image
            else:
                # This code created extra
                frame = FabioFrame(image.data, image.header)

        frame._set_container(self, num)
        frame._set_file_container(self, num)
        return frame

    def frames(self):
        """Iterate all available frames stored in this image container.

        :rtype: Iterator[FabioFrame]
        """
        for num in range(self.nframes):
            frame = self._get_frame(num)
            yield frame

    @property
    def shape(self):
        if self._shape is not None:
            return self._shape
        return self.data.shape

    @shape.setter
    def shape(self, value):
        if self.data is not None:
            self.data.shape = value
        else:
            self._shape = value

    @property
    def dtype(self):
        return self.data.dtype

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
        if self.filename is None:
            raise IOError()
        return openimage(fabioutils.previous_filename(self.filename))

    def next(self):
        """Returns the next file in the series as a fabioimage

        :raise IOError: When there is no next file in the series.
        """
        from .openimage import openimage
        if self.filename is None:
            raise IOError()
        return openimage(
            fabioutils.next_filename(self.filename))

    def getheader(self):
        """ returns self.header """
        return self.header

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

    def rebin(self, x_rebin_fact, y_rebin_fact, keep_I=True):
        """
        Rebin the data and adjust dims

        :param int x_rebin_fact: x binning factor
        :param int y_rebin_fact: y binning factor
        :param bool keep_I: shall the signal increase ?
        """
        if self.data is None:
            raise Exception('Please read in the file you wish to rebin first')

        dim2, dim1 = self.data.shape
        if (dim1 % x_rebin_fact != 0) or (dim2 % y_rebin_fact != 0):
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

        self._shape = None

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
            codec_name = dest + "image"
            from . import fabioformats
            codec_class = fabioformats.get_class_by_name(codec_name)
            if codec_class is not None:
                other = fabioformats.factory(codec_name)
            else:
                # load modules which could be suitable:
                for class_ in fabioformats.get_classes_from_extension(dest):
                    try:
                        other = class_()
                    except Exception:
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
            except (IOError, IndexError):
                break


fabioimage = FabioImage
