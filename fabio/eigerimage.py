# coding: utf-8
#
#    Project: FabIO X-ray image reader
#
#    Copyright (C) 2010-2016 European Synchrotron Radiation Facility
#                       Grenoble, France
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

"""Eiger data/master file reader for FabIO

Eiger data files are HDF5 files with one group called "entry" and a dataset
called "data" in it (now in a data group).

Those dataset are usually compressed using LZ4 and/or bitshuffle compression:

* https://github.com/nexusformat/HDF5-External-Filter-Plugins/tree/master/LZ4
* https://github.com/kiyo-masui/bitshuffle

H5py (>2.5) and libhdf5 (>1.8.10) with the corresponding compression plugin are needed to
actually read the data.
Under windows, those plugins can easily be installed via this repository:
https://github.com/silx-kit/hdf5plugin

"""

__authors__ = ["Jérôme Kieffer"]
__contact__ = "jerome.kieffer@esrf.fr"
__license__ = "MIT"
__copyright__ = "ESRF"
__date__ = "05/07/2022"

import logging
logger = logging.getLogger(__name__)
import posixpath
import numpy
try:
    import h5py
except ImportError:
    h5py = None

from .fabioimage import FabioImage
from .fabioutils import NotGoodReader
from .nexus import Nexus
try:
    import hdf5plugin
except ImportError:
    hdf5plugin = None


class EigerImage(FabioImage):
    """
    FabIO image class for Images from Eiger data files (HDF5)
    """

    DESCRIPTION = "Eiger data files based on HDF5"

    DEFAULT_EXTENSIONS = ["h5", "hdf5"]

    def __init__(self, data=None, header=None):
        """
        Set up initial values
        """
        if not h5py:
            raise RuntimeError("fabio.EigerImage cannot be used without h5py. Please install h5py and restart")
        if data is None:
            self.dataset = [None]
        else:
            if data.ndim < 3:
                data = data.reshape(*([1] * (3 - data.ndim) + list(data.shape)))
            else:
                data = data.reshape(*([-1] + list(data.shape[-2:])))
            self.dataset = [data]
            self._data = data[0,:,:]
        FabioImage.__init__(self, None, header)
        self.h5 = None

    def __repr__(self):
        if self.h5 is not None:
            return "Eiger dataset with %i frames from %s" % (self.nframes, self.h5.filename)
        else:
            return "%s object at %s" % (self.__class__.__name__, hex(id(self)))

    def _readheader(self, infile):
        """
        Read and decode the header of an image:

        :param infile: Opened python file (can be stringIO or bzipped file)
        """
        # list of header key to keep the order (when writing)
        self.header = self.check_header()
        infile.seek(0)

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
        lstds = []
        # read the image data
        self.h5 = h5py.File(fname, mode="r")
        if "entry" in self.h5:
            entry = self.h5["entry"]
            if "data" in entry:
                data = entry["data"]
                if isinstance(data, h5py.Group):
                    "Newer format /entry/data/data_000001"
                    datasets = [i for i in data.keys() if i.startswith("data")]
                    datasets.sort()
                    try:
                        for i in datasets:
                            lstds.append(data[i])
                    except KeyError:
                        pass

                else:
                    lstds = [data]
            else:
                "elder format entry/data_01"
                datasets = [i for i in entry.keys() if i.startswith("data")]
                datasets.sort()
                try:
                    for i in datasets:
                        lstds.append(entry[i])
                except KeyError:
                    pass
        if lstds:
            self.dataset = lstds
        else:
            raise NotGoodReader("HDF5 file does not contain an Eiger-like structure.")

        if frame is not None:
            return self.getframe(int(frame))
        else:
            self.currentframe = 0

            self._data = self.dataset[0][self.currentframe,:,:]
            self._shape = None
            return self

    def write(self, fname):
        """
        try to write image
        :param fname: name of the file
        """
        if hdf5plugin is None:
            logger.warning("hdf5plugin is needed for bitshuffle-LZ4 compression, falling back on gzip (slower)")
            compression = {"compression":"gzip",
                   "compression_opts":1}
        else:
            compression = hdf5plugin.Bitshuffle()

        with Nexus(fname, mode="w") as nxs:
            entry = nxs.new_entry(entry="entry", program_name=None, force_name=True)
            data_grp = nxs.new_class(entry, "data", "NXdata")
            entry.attrs["default"] = "data"
            nxs.h5.attrs["default"] = "entry"
            for i, ds in enumerate(self.dataset):
                if ds is None:
                    # we are in a trouble
                    data = numpy.atleast_2d(numpy.NaN)
                elif isinstance(ds, h5py.Dataset):
                    data = numpy.atleat_2d(ds[()])
                else:
                    data = numpy.atleast_2d(ds)
                if len(data.shape) == 2:
                    data.shape = (1,) + data.shape
                chunks = (1,) + data.shape[-2:]
                if len(self.dataset) > 1:
                    hds = data_grp.create_dataset(f"data_{i+1:06d}", data=data, chunks=chunks, **compression)
                elif len(self.dataset) == 1:
                    hds = data_grp.create_dataset(f"data", data=data, chunks=chunks, **compression)
                hds.attrs["interpretation"] = "image"
                if "signal" not in data_grp.attrs:
                    data_grp.attrs["signal"] = posixpath.split(hds.name)[-1]

    def getframe(self, num):
        """ returns the frame numbered 'num' in the stack if applicable"""
        if self.nframes > 1:
            new_img = None
            if (num >= 0) and num < self.nframes:
                if isinstance(self.dataset, list):
                    nfr = num
                    for ds in self.dataset:
                        if ds is None or ds.ndim == 2:
                            if nfr == 0:
                                data = None
                            else:
                                nfr -= 1
                        elif ds.ndim == 3:
                            # Stack of images
                            if (nfr < ds.shape[0]):
                                data = ds[nfr]
                                break
                            else:
                                nfr -= ds.shape[0]

                else:
                    data = self.dataset[num]
                new_img = self.__class__(data=None, header=self.header)
                new_img._data = data
                new_img.dataset = self.dataset
                new_img.h5 = self.h5
                new_img._nframes = self.nframes
                new_img.currentframe = num
            else:
                raise IOError(f"getframe {num} out of range [0 {self.nframes}[")
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
            self.dataset = []

    @property
    def nframes(self):
        """Returns the number of frames contained in this file

        :rtype: int
        """
        return sum(i.shape[0] if i.ndim > 2 else 1 for i in self.dataset)

    def get_data(self):
        if self._data is None:
            data = None
            index = self.currentframe
            if isinstance(self.dataset, list):
                frame_idx = [len(ds) if (ds is not None and ds.ndim == 3) else 1 for ds in self.dataset]
                end_ds = numpy.cumsum(frame_idx)
                for idx, end in enumerate(end_ds):
                    start = 0 if idx == 0 else end_ds[idx - 1]
                    if end > index >= start:
                        ds = self.dataset[idx]
                        if ds is None or ds.ndim == 2:
                            data = ds
                        else:
                            data = ds[index - start]
            else:
                data = self.dataset[index]
            self._data = data
        return self._data

    def set_data(self, data, index=None):
        """Set the data for frame index

        :param data: numpy array
        :param int index: index of the frame (by default: current one)
        :raises IndexError: If the frame number is out of the available range.
        """
        if data is None:
            return
        if index is None:
            index = self.currentframe
        if isinstance(self.dataset, list):
            frame_idx = [len(ds) if (ds is not None and ds.ndim == 3) else 1 for ds in self.dataset]
            end_ds = numpy.cumsum(frame_idx)
            nframes = end_ds[-1]
            if index == nframes:
                self.dataset.append(data)

            elif index > nframes:
                # pad dataset with None ?
                self.dataset += [None] * (1 + index - len(self.dataset))
                self.dataset[index] = data
            else:
                for idx, end in enumerate(end_ds):
                    start = 0 if idx == 0 else end_ds[idx - 1]
                    if end > index >= start:
                        ds = self.dataset[idx]
                        if ds is None or ds.ndim == 2:
                            self.dataset[idx] = data
                        else:
                            ds[index - start] = data
        if index == self.currentframe:
            self._data = data

    data = property(get_data, set_data)


eigerimage = EigerImage
