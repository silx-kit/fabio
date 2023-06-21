# coding: utf-8
#
#    Project: X-ray image reader
#             https://github.com/silx-kit/fabio
#
#    Copyright 2020-2021(C) European Synchrotron Radiation Facility, Grenoble, France
#
#  Permission is hereby granted, free of charge, to any person
#  obtaining a copy of this software and associated documentation files
#  (the "Software"), to deal in the Software without restriction,
#  including without limitation the rights to use, copy, modify, merge,
#  publish, distribute, sublicense, and/or sell copies of the Software,
#  and to permit persons to whom the Software is furnished to do so,
#  subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be
#  included in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
#  OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#  NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#  HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
#  WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#  OTHER DEALINGS IN THE SOFTWARE.

"""Image format generated with sparsify-Bragg from pyFAI

This format contains the average background with its associated deviation in addition to all
pixels corresponding to Bragg peaks (positive outliers)

This class is able to regenerate images with or without background noise.  
"""

__authors__ = ["Jérôme Kieffer"]
__contact__ = "jerome.kieffer@esrf.fr"
__license__ = "MIT"
__copyright__ = "2020 ESRF"
__date__ = "09/02/2023"

import logging
logger = logging.getLogger(__name__)
import numpy
try:
    import h5py
except ImportError:
    h5py = None
else:
    try:
        import hdf5plugin
    except:
        pass
from .fabioutils import NotGoodReader
from .fabioimage import FabioImage, OrderedDict
try:
    from .ext import dense as cython_densify
except ImportError:
    cython_densify = None


def densify(mask,
            radius,
            index,
            intensity,
            dummy,
            background,
            background_std=None,
            normalization=None,
            seed=None):
    """Generate a dense image of its sparse representation
    
    :param mask: 2D array with NaNs for mask and pixel radius for the valid pixels
    :param radius: 1D array with the radial distance
    :param index: position of non-background pixels
    :param intensity: intensities of non background pixels (at index position)
    :param dummy: numerical value for masked-out pixels in dense image
    :return: dense frame as 2D array
    :param background: 1D array with the background values at given distance from the center
    :param background_std: 1D array with the background std at given distance from the center
    :param normalization: flat*solidangle*polarization*... array
    :param seed: numerical seed for random number generator
    :return dense array
    """
    dense = numpy.interp(mask, radius, background)
    if background_std is not None:
        if seed is not None:
            numpy.random.seed(seed)
        std = numpy.interp(mask, radius, background_std)
        numpy.maximum(0.0, numpy.random.normal(dense, std), out=dense)
    if normalization is not None:
        dense *= normalization

    flat = dense.ravel()
    flat[index] = intensity
    dtype = intensity.dtype
    if numpy.issubdtype(dtype, numpy.integer):
        # Foolded by banker's rounding !!!!
        dense +=0.5
        numpy.floor(dense, out=dense)
    dense = numpy.ascontiguousarray(dense, dtype=dtype)
    dense[numpy.logical_not(numpy.isfinite(mask))] = dummy
    return dense


class SparseImage(FabioImage):
    """FabIO image class for images compressed by sparsification of Bragg peaks 

    While the sparsification requires pyFAI and substential resources, re-densifying the data is easy.
    
    The program used for the sparsification is `sparsify-Bragg` from the pyFAI suite
    
    Set the noisy attribute to re-generate background noise
    """

    DESCRIPTION = "spasify-Bragg"

    DEFAULT_EXTENSIONS = [".h5", ".hdf5", ".nxs"]

    NOISY = False

    def __init__(self, *arg, **kwargs):
        """
        Generic constructor
        """
        if not h5py:
            raise RuntimeError("fabio.SparseImage cannot be used without h5py. Please install h5py and restart")

        FabioImage.__init__(self, *arg, **kwargs)
        self.mask = None
        self.normalization = None  # Correspond to the flat/polarization/solid-angle correction
        self.radius = None
        self.background_avg = None
        self.background_std = None
        self.frame_ptr = None
        self.index = None
        self.intensity = None
        self.dummy = None
        self.noisy = float(self.__class__.NOISY)
        self.h5 = None

    def close(self):
        if self.h5 is not None:
            self.h5.close()
            self.dataset = None

    def _readheader(self, infile):
        """
        Read and decode the header of an image:

        :param infile: Opened python file (can be stringIO or bzipped file)
        """
        # list of header key to keep the order (when writing)
        self.header = self.check_header()

    def read(self, fname, frame=None):
        """
        Try to read image

        :param fname: name of the file
        :param frame: number of the frame
        """

        self.resetvals()
        self._readheader(fname)
        self.h5 = h5py.File(fname, mode="r")
        default_entry = self.h5.attrs.get("default")
        if default_entry is None or default_entry not in self.h5:
            raise NotGoodReader("HDF5 file does not contain any default entry.")
        entry = self.h5[default_entry]
        default_data = entry.attrs.get("pyFAI_sparse_frames") or entry.attrs.get("default")
        if default_data is None or default_data not in entry:
            raise NotGoodReader("HDF5 file does not contain any default NXdata.")
        nx_data = entry[default_data]
        self.mask = nx_data["mask"][()]
        self.radius = nx_data["radius"][()]
        self.background_avg = nx_data["background_avg"][()]
        self.background_std = nx_data["background_std"][()]
        self.frame_ptr = nx_data["frame_ptr"][()]
        self.index = nx_data["index"][()]
        self.intensity = nx_data["intensity"][()]
        try:
            self.dummy = self.intensity.dtype.type(nx_data["dummy"][()])
        except KeyError:
            if self.intensity.dtype.char in numpy.typecodes['AllFloat']:
                self.dummy = numpy.NaN
            else:
                self.dummy = 0
            
        self._nframes = self.frame_ptr.shape[0] - 1
        if "normalization" in nx_data:
            self.normalization = numpy.ascontiguousarray(nx_data["normalization"][()], dtype=numpy.float32)

        if frame is not None:
            return self.getframe(int(frame))
        else:
            self.currentframe = 0
            self.data = self._generate_data(self.currentframe)
            self._shape = None
            return self

    def _generate_data(self, index=0):
        "Actually rebuilds the data for one frame"
        if self.h5 is None:
            logger.warning("Not data have been read from disk")
            return
        start, stop = self.frame_ptr[index:index + 2]
        if cython_densify is not None:
            return cython_densify.densify(self.mask,
                                 self.radius,
                                 self.index[start:stop],
                                 self.intensity[start:stop],
                                 self.dummy,
                                 self.intensity.dtype,
                                 self.background_avg[index],
                                 self.background_std[index] * self.noisy if self.noisy else None,
                                 self.normalization)
        else:
            # Fall-back on numpy code.
            return densify(self.mask,
                           self.radius,
                           self.index[start:stop],
                           self.intensity[start:stop],
                           self.dummy,
                           self.background_avg[index],
                           self.background_std[index] * self.noisy if self.noisy else None,
                           self.normalization)

    def getframe(self, num):
        """ returns the frame numbered 'num' in the stack if applicable"""
        if self.nframes > 1:
            new_img = None
            if (num >= 0) and num < self.nframes:
                data = self._generate_data(num)
                new_img = self.__class__(data=data, header=self.header)
                new_img.mask = self.mask
                new_img.radius = self.radius
                new_img.background_avg = self.background_avg
                new_img.background_std = self.background_std
                new_img.frame_ptr = self.frame_ptr
                new_img.index = self.index
                new_img.intensity = self.intensity
                new_img.dummy = self.dummy
                new_img.noisy = self.noisy
                new_img.h5 = self.h5
                new_img._nframes = self.nframes
                new_img.currentframe = num
                new_img.normalization = self.normalization
            else:
                raise IOError("getframe %s out of range [%s %s[" % (num, 0, self.nframes))
        else:
            new_img = FabioImage.getframe(self, num)
        return new_img

    def previous(self):
        """ returns the previous frame in the series as a fabioimage """
        return self.getframe(self.currentframe - 1)

    def next(self):
        """ returns the next frame in the series as a fabioimage """
        return self.getframe(self.currentframe + 1)


# This is for compatibility with old code:
sparseimage = SparseImage
