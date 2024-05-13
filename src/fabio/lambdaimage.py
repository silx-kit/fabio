# coding: utf-8
#
#    Project: X-ray image reader
#             https://github.com/silx-kit/fabio
#
#    Copyright (C) European Synchrotron Radiation Facility, Grenoble, France
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

"""
Basic read support for NeXus/HDF5 files saved by Lambda-detectors. 
"""

__authors__ = ["Jérôme Kieffer"]
__contact__ = "jerome.kieffer@esrf.fr"
__license__ = "MIT"
__copyright__ = "ESRF"
__date__ = "02/05/2024"

import logging
logger = logging.getLogger(__name__)
import posixpath
import os
import numpy
from .fabioimage import FabioImage
from .fabioutils import NotGoodReader
from . import nexus
try:
    import h5py
except ImportError:
    h5py = None
try:
    import hdf5plugin
except ImportError:
    hdf5plugin = None


class LambdaImage(FabioImage):
    """FabIO image class for Images for Lambda detector

    Lambda detector are medipix based detectors sold by X-Spectrum: 
    https://x-spectrum.de/products/lambda/
    """

    DESCRIPTION = "HDF5 file produces by Lambda"

    DEFAULT_EXTENSIONS = ["h5", "hdf5", "nxs"]
    DETECTOR_GRP = "/entry/instrument/detector"

    def __init__(self, data=None, header=None):
        """
        Set up initial values
        """
        if not h5py:
            raise RuntimeError("fabio.LambdaImage cannot be used without h5py. Please install h5py and restart")

        self.dataset = [data]
        self._data = None
        FabioImage.__init__(self, data, header)
        self.h5 = None

    @property
    def nframes(self):
        """Returns the number of frames contained in this file

        :rtype: int
        """
        return len(self.dataset)

    def get_data(self):
        if self._data is None and len(self.dataset) >= self.currentframe:
            self._data = self.dataset[self.currentframe]
        return self._data

    def set_data(self, data, index=None):
        """Set the data for frame index

        :param data: numpy array
        :param int index: index of the frame (by default: current one)
        :raises IndexError: If the frame number is out of the available range.
        """
        if index is None:
            index = self.currentframe
        if isinstance(self.dataset, list):
            if index == len(self.dataset):
                self.dataset.append(data)
            elif index > len(self.dataset):
            # pad dataset with None ?
                self.dataset += [None] * (1 + index - len(self.dataset))
                self.dataset[index] = data
            else:
                self.dataset[index] = data
        if index == self.currentframe:
            self._data = data

    data = property(get_data, set_data)

    def __repr__(self):
        if self.h5 is None:
            return "%s object at %s" % (self.__class__.__name__, hex(id(self)))
        else:
            return "Lambda/nexus dataset with %i frames from %s" % (self.nframes, self.h5.filename)

    def _readheader(self, infile):
        """
        Read and decode the header of an image:

        :param infile: Opened python file (can be stringIO or bzipped file)
        """
        # list of header key to keep the order (when writing)
        self.header = self.check_header()
        data_path = posixpath.join(self.DETECTOR_GRP, "data")
        description_path = posixpath.join(self.DETECTOR_GRP, "description")
        name_path = posixpath.join(self.DETECTOR_GRP, "local_name")
        with h5py.File(infile, mode="r") as h5:
            if not (data_path in h5 and description_path in h5):
                raise NotGoodReader("HDF5's does not look like a Lambda-detector NeXus file.")
            description = h5[description_path][()]
            if isinstance(description, bytes):
                description = description.decode()
            else:
                description = str(description)
            if description != "Lambda":
                raise NotGoodReader("Nexus file does not look like it has been written by a Lambda-detector.")
            if name_path in h5:
                self.header["detector"] = str(h5[name_path][()]) 
            else:
                self.header["detector"] = "detector"

    def read(self, fname, frame=None):
        """
        Try to read image

        :param fname: name of the file
        :param frame: number of the frame
        """

        self.resetvals()
        with self._open(fname) as infile:
            self._readheader(infile)
            # read the image data and declare it

        self.dataset = None
        # read the image data
        self.h5 = h5py.File(fname, mode="r")
        data_path = posixpath.join(self.DETECTOR_GRP, "data")
        if data_path in self.h5:
            ds = self.h5[data_path]
        else:
            raise NotGoodReader("HDF5's default entry does not exist.")
        self.dataset = ds
        self._nframes = ds.shape[0]

        if frame is not None:
            return self.getframe(int(frame))
        else:
            self.currentframe = 0
            self.data = self.dataset[self.currentframe]
            self._shape = None
            return self

    def getframe(self, num):
        """ returns the frame numbered 'num' in the stack if applicable"""
        if self.nframes > 1:
            new_img = None
            if (num >= 0) and num < self.nframes:
                data = self.dataset[num]
                new_img = self.__class__(data=data, header=self.header)
                new_img.dataset = self.dataset
                new_img.h5 = self.h5
                new_img._nframes = self.nframes
                new_img.currentframe = num
            else:
                raise IOError(f"getframe({num}) out of range [0, {self.nframes}[")
        else:
            new_img = FabioImage.getframe(self, num)
        return new_img

    def previous(self):
        """ returns the previous file in the series as a FabioImage """
        new_image = None
        if self.nframes == 1:
            new_image = FabioImage.previous(self)
        else:
            new_idx = self.currentframe - 1
            new_image = self.getframe(new_idx)
        return new_image

    def next(self):
        """Returns the next file in the series as a fabioimage

        :raise IOError: When there is no next file or image in the series.
        """
        new_image = None
        if self.nframes == 1:
            new_image = FabioImage.next(self)
        else:
            new_idx = self.currentframe + 1
            new_image = self.getframe(new_idx)
        return new_image

    def close(self):
        if self.h5 is not None:
            self.h5.close()
            self.dataset = None

    def write(self, filename):
        """Write a file that looks like one saved by Lambda-detector."""
        start_time = nexus.get_isotime()
        abs_name = os.path.abspath(filename)
        mode = "w"
        if hdf5plugin is None:
            logger.warning("hdf5plugin is needed for bitshuffle-LZ4 compression, falling back on gzip (slower)")
            compression = {"compression":"gzip",
                           "compression_opts":1}
        else:
            compression = hdf5plugin.Bitshuffle()

        with nexus.Nexus(abs_name, mode=mode) as nxs:
            entry = nxs.new_entry(entry="entry",
                                  program_name=None,
                                  force_time=start_time,
                                  force_name=True)
            instrument_grp = nxs.new_class(entry, "instrument", class_type="NXinstrument")
            detector_grp = nxs.new_class(instrument_grp, "detector", class_type="NXdetector")
            detector_grp["description"] = b"Lambda"
            detector_grp["local_name"] = self.header.get("detector", "detector").encode()
            detector_grp["layout"] = "X".join(str(i) for i in self.shape[-1::-1]).encode()
            header_grp = nxs.new_class(detector_grp, "collection", class_type="NXcollection")
            acq_grp = nxs.new_class(detector_grp, "acquisition", class_type="NXcollection")

            acq_grp["frame_numbers"] = numpy.int32(self.nframes)

            shape = (self.nframes,) + self.shape
            dataset = detector_grp.create_dataset("data", shape=shape, chunks=(1,) + self.shape, dtype=self.dtype, **compression)
            dataset.attrs["interpretation"] = "image"
            for i, frame in enumerate(self.dataset):
                dataset[i] = frame

# This is for compatibility with old code:
lambdaimage = LambdaImage
