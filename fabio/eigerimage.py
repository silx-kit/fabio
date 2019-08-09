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

from __future__ import with_statement, print_function, division

__authors__ = ["Jérôme Kieffer"]
__contact__ = "jerome.kieffer@esrf.fr"
__license__ = "MIT"
__copyright__ = "ESRF"
__date__ = "01/03/2019"

import logging
logger = logging.getLogger(__name__)

try:
    import h5py
except ImportError:
    h5py = None

from .fabioimage import FabioImage
from .fabioutils import NotGoodReader


class EigerImage(FabioImage):
    """
    FabIO image class for Images from Eiger data files (HDF5)
    """

    DESCRIPTION = "Eiger data files based on HDF5"

    DEFAULT_EXTENSIONS = ["h5"]

    def __init__(self, data=None, header=None):
        """
        Set up initial values
        """
        if not h5py:
            raise RuntimeError("fabio.EigerImage cannot be used without h5py. Please install h5py and restart")

        FabioImage.__init__(self, data, header)
        self.dataset = [data]
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
        try to read image
        :param fname: name of the file
        """

        self.resetvals()
        with self._open(fname) as infile:
            self._readheader(infile)

        self.dataset = None
        lstds = []
        # read the image data
        self.h5 = h5py.File(fname, mode="r")
        if "entry" in self.h5:
            entry = self.h5["entry"]
            if "data" in entry:
                data = entry["data"]
                if isinstance(data, h5py.Group):
                    "Newer format /entry/data/data_1"
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

        if not lstds:
            raise NotGoodReader("HDF5 file does not contain an Eiger-like structure.")

        self.dataset = lstds
        self._nframes = sum(i.shape[0] for i in lstds)

        if frame is not None:
            return self.getframe(int(frame))
        else:
            self.currentframe = 0
            self.data = self.dataset[0][self.currentframe, :, :]
            self._shape = None
            return self

    def write(self, fname):
        """
        try to write image
        :param fname: name of the file
        """
        if len(self.dataset.shape) == 2:
            self.dataset.shape = (1,) + self.dataset.shape
        with h5py.File(fname) as h5file:
            grp = h5file.require_group("entry/data")
            if len(self.dataset) > 1:
                for i, ds in enumerate(self.dataset):
                    grp["data_%06i" % i] = ds
            else:
                grp["data"] = self.dataset

    def getframe(self, num):
        """ returns the frame numbered 'num' in the stack if applicable"""
        if self.nframes > 1:
            new_img = None
            if (num >= 0) and num < self.nframes:
                if isinstance(self.dataset, list):
                    nfr = num
                    for ds in self.dataset:
                        if nfr < ds.shape[0]:
                            data = ds[nfr]
                            break
                        else:
                            nfr -= ds.shape[0]
                else:
                    data = self.dataset[num]
                new_img = self.__class__(data=data, header=self.header)
                new_img.dataset = self.dataset
                new_img.h5 = self.h5
                new_img._nframes = self.nframes
                new_img.currentframe = num
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

    def close(self):
        if self.h5 is not None:
            self.h5.close()
            self.dataset = None


eigerimage = EigerImage
