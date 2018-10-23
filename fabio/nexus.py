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
"""Module for handling HDF5 data structure following the NeXuS convention

Stand-alone module which tries to offer interface to HDF5 via H5Py

"""
from __future__ import absolute_import, print_function, division

__author__ = "Jerome Kieffer"
__contact__ = "Jerome.Kieffer@ESRF.eu"
__license__ = "MIT"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__date__ = "22/10/2018"
__status__ = "beta"
__docformat__ = 'restructuredtext'

import logging
import numpy
import os
import sys
import time

from .fabioutils import exists
from ._version import version
from .third_party import six

logger = logging.getLogger(__name__)
try:
    import h5py
except ImportError as error:
    h5py = None
    logger.error("h5py module missing")
else:
    try:
        h5py._errors.silence_errors()
    except AttributeError:  # old h5py
        pass


def get_isotime(force_time=None):
    """
    :param force_time: enforce a given time (current by default)
    :type force_time: float
    :return: the current time as an ISO8601 string
    :rtype: string
    """
    if force_time is None:
        force_time = time.time()
    localtime = time.localtime(force_time)
    gmtime = time.gmtime(force_time)
    tz_h = localtime.tm_hour - gmtime.tm_hour
    tz_m = localtime.tm_min - gmtime.tm_min
    return "%s%+03i:%02i" % (time.strftime("%Y-%m-%dT%H:%M:%S", localtime), tz_h, tz_m)


def from_isotime(text, use_tz=False):
    """
    :param text: string representing the time is iso format
    :return: Time in second since epoch (float)
    """
    if isinstance(text, numpy.ndarray):
        text = text[0]
    if six.PY3 and isinstance(text, six.binary_type):
        text = text.decode("utf-8")
    else:
        text = str(text)
    base = text[:19]
    if use_tz and len(text) == 25:
        sgn = 1 if text[:19] == "+" else -1
        tz = 60 * (60 * int(text[20:22]) + int(text[23:25])) * sgn
    else:
        tz = 0
    return time.mktime(time.strptime(base, "%Y-%m-%dT%H:%M:%S")) + tz


def is_hdf5(filename):
    """
    Check if a file is actually a HDF5 file

    :param filename: this file has better to exist
    :return: true or False
    """
    signature = b"\x89\x48\x44\x46\x0d\x0a\x1a\x0a"
    if not exists(filename):
        raise IOError("No such file %s" % (filename))
    with open(filename.split("::")[0], "rb") as f:
        sig = f.read(len(signature))
    return sig == signature


class Nexus(object):
    """
    Writer class to handle Nexus/HDF5 data
    Manages:
    entry
        pyFAI-subentry
            detector

    #TODO: make it thread-safe !!!
    """
    def __init__(self, filename, mode="r"):
        """
        Constructor

        :param filename: name of the hdf5 file containing the nexus
        :param mode: can be r or a
        """
        self.filename = os.path.abspath(filename)
        self.mode = mode
        if not h5py:
            logger.error("h5py module missing: NeXus not supported")
            raise RuntimeError("H5py module is missing")
        if exists(self.filename) and self.mode == "r":
            self.h5 = h5py.File(self.filename.split("::")[0], mode=self.mode)
        else:
            self.h5 = h5py.File(self.filename.split("::")[0])
        self.to_close = []

    def close(self, endtime=None):
        """Close the filename and update all entries

        :param endtime: timestamp in iso-format of the end of the acquisition.
        """
        if endtime is None:
            end_time = get_isotime()
        elif isinstance(endtime, (int, float)):
            end_time = get_isotime(endtime)
        for entry in self.to_close:
            entry["end_time"] = end_time
        self.h5.close()

    # Context manager for "with" statement compatibility
    def __enter__(self, *arg, **kwarg):
        return self

    def __exit__(self, *arg, **kwarg):
        self.close()

    def get_entry(self, name):
        """
        Retrieves an entry from its name

        :param name: name of the entry to retrieve
        :return: HDF5 group of NXclass == NXentry
        """
        for grp_name in self.h5:
            if grp_name == name:
                grp = self.h5[grp_name]
                if (isinstance(grp, h5py.Group) and
                        "start_time" in grp and
                        "NX_class" in grp.attrs and
                        grp.attrs["NX_class"] == "NXentry"):
                    return grp

    def get_entries(self):
        """
        retrieves all entry sorted the latest first.

        :return: list of HDF5 groups
        """
        entries = [(grp, from_isotime(self.h5[grp + "/start_time"].value))
                   for grp in self.h5
                   if (isinstance(self.h5[grp], h5py.Group) and
                       "start_time" in self.h5[grp] and
                       "NX_class" in self.h5[grp].attrs and
                       self.h5[grp].attrs["NX_class"] == "NXentry")]
        if entries:
            entries.sort(key=lambda a: a[1], reverse=True)  # sort entries in decreasing time
            return [self.h5[i[0]] for i in entries]
        else:  # no entries found, try without sorting by time
            entries = [grp for grp in self.h5
                       if (isinstance(self.h5[grp], h5py.Group) and
                           "NX_class" in self.h5[grp].attrs and
                           self.h5[grp].attrs["NX_class"] == "NXentry")]
            entries.sort(reverse=True)
            return [self.h5[i] for i in entries]

    def find_detector(self, all=False):
        """
        Tries to find a detector within a NeXus file, takes the first compatible detector

        :param all: return all detectors found as a list
        """
        result = []
        for entry in self.get_entries():
            for instrument in self.get_class(entry, "NXsubentry") + self.get_class(entry, "NXinstrument"):
                for detector in self.get_class(instrument, "NXdetector"):
                    if all:
                        result.append(detector)
                    else:
                        return detector
        return result

    def find_data(self, all=False):
        """
        Tries to find a NXdata within a NeXus file

        :param all: return all detectors found as a list
        """
        result = []
        for entry in self.get_entries():
            data = self.get_data(entry)
            if data:
                if all:
                    result += data
                else:
                    return data[0]
            for instrument in self.get_class(entry, "NXinstrument"):
                data = self.get_data(instrument)
                if data:
                    if all:
                        result += data
                    else:
                        return data[0]
                for detector in self.get_class(instrument, "NXdetector"):
                    data = self.get_data(detector)
                    if data:
                        if all:
                            result += data
                        else:
                            return data[0]
            for instrument in self.get_class(entry, "NXsubentry"):
                data = self.get_data(instrument)
                if data:
                    if all:
                        result += data
                    else:
                        return data[0]
                for detector in self.get_class(instrument, "NXdetector"):
                    data = self.get_data(detector)
                    if data:
                        if all:
                            result += data
                        else:
                            return data[0]

        return result

    def new_entry(self, entry="entry", program_name="pyFAI",
                  title="description of experiment",
                  force_time=None, force_name=False):
        """
        Create a new entry

        :param entry: name of the entry
        :param program_name: value of the field as string
        :param title: value of the field as string
        :param force_time: seconds since epoch enforce the start_time
        :param force_name: set to true to prevent the addition of a _0001 suffix
        :return: the corresponding HDF5 group
        """
        if force_name:
            entry_grp = self.h5.require_group(entry)
        else:
            nb_entries = len(self.get_entries())
            entry_grp = self.h5.require_group("%s_%04i" % (entry, nb_entries))
        entry_grp.attrs["NX_class"] = "NXentry"
        entry_grp["title"] = numpy.string_(title)
        entry_grp["program_name"] = numpy.string_(program_name)
        entry_grp["start_time"] = numpy.string_(get_isotime(force_time))
        self.to_close.append(entry_grp)
        return entry_grp

    def new_instrument(self, entry="entry", instrument_name="id00",):
        """
        Create an instrument in an entry or create both the entry and the instrument if
        """
        if not isinstance(entry, h5py.Group):
            entry = self.new_entry(entry)
        return self.new_class(entry, instrument_name, "NXinstrument")
#        howto external link
        # myfile['ext link'] = h5py.ExternalLink("otherfile.hdf5", "/path/to/resource")

    def new_class(self, grp, name, class_type="NXcollection"):
        """
        create a new sub-group with  type class_type
        :param grp: parent group
        :param name: name of the sub-group
        :param class_type: NeXus class name
        :return: subgroup created
        """
        sub = grp.require_group(name)
        sub.attrs["NX_class"] = class_type
        return sub

    def new_detector(self, name="detector", entry="entry", subentry="pyFAI"):
        """
        Create a new entry/pyFAI/Detector

        :param detector: name of the detector
        :param entry: name of the entry
        :param subentry: all pyFAI description of detectors should be in a pyFAI sub-entry
        """
        entry_grp = self.new_entry(entry)
        pyFAI_grp = self.new_class(entry_grp, subentry, "NXsubentry")
        pyFAI_grp["definition_local"] = numpy.string_("pyFAI")
        pyFAI_grp["definition_local"].attrs["version"] = version
        det_grp = self.new_class(pyFAI_grp, name, "NXdetector")
        return det_grp

    def get_class(self, grp, class_type="NXcollection"):
        """
        return all sub-groups of the given type within a group

        :param grp: HDF5 group
        :param class_type: name of the NeXus class
        """
        coll = [grp[name] for name in grp
                if (isinstance(grp[name], h5py.Group) and
                    "NX_class" in grp[name].attrs and
                    grp[name].attrs["NX_class"] == class_type)]
        return coll

    def get_data(self, grp, class_type="NXdata"):
        """
        return all dataset of the the NeXus class NXdata

        :param grp: HDF5 group
        :param class_type: name of the NeXus class
        """
        result = []
        for grp in self.get_class(grp, class_type):
            result += [grp[name] for name in grp
                       if (isinstance(grp[name], h5py.Dataset) and
                       ("signal" in grp[name].attrs))]
        return result

    def deep_copy(self, name, obj, where="/", toplevel=None, excluded=None, overwrite=False):
        """
        perform a deep copy:
        create a "name" entry in self containing a copy of the object

        :param where: path to the toplevel object (i.e. root)
        :param  toplevel: firectly the top level Group
        :param excluded: list of keys to be excluded
        :param overwrite: replace content if already existing
        """
        if (excluded is not None) and (name in excluded):
            return
        if not toplevel:
            toplevel = self.h5[where]
        if isinstance(obj, h5py.Group):
            if name not in toplevel:
                grp = toplevel.require_group(name)
                for k, v in obj.attrs.items():
                        grp.attrs[k] = v
        elif isinstance(obj, h5py.Dataset):
            if name in toplevel:
                if overwrite:
                    del toplevel[name]
                    logger.warning("Overwriting %s in %s" % (toplevel[name].name, self.filename))
                else:
                    logger.warning("Not overwriting %s in %s" % (toplevel[name].name, self.filename))
                    return
            toplevel[name] = obj.value
            for k, v in obj.attrs.items():
                toplevel[name].attrs[k] = v
