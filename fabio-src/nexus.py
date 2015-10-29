# coding: utf-8
#
#    Project: X-ray image reader
#             https://github.com/kif/fabio
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


from __future__ import absolute_import, print_function, division

__author__ = "Jerome Kieffer"
__contact__ = "Jerome.Kieffer@ESRF.eu"
__license__ = "GPLv3+"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__date__ = "29/10/2015"
__status__ = "beta"
__docformat__ = 'restructuredtext'
__doc__ = """

Module for handling HDF5 data structure following the NeXuS convention

Stand-alone module which tries to offer interface to HDF5 via H5Py

"""
import fabio
import json
import logging
import numpy
import os
import posixpath
import sys
import threading
import time

from ._version import version

if sys.version_info[0] < 3:
    bytes = str
    from urlparse import urlparse
else:
    from urllib.parse import  urlparse


logger = logging.getLogger("fabio.nexus")
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


def exists(fname):
    """
    Return True if the filename or dataset locator exist and is valid
    @param fname: filename or url as a string

    example of url: "hdf5:///example.h5?entry/instrument/data#slice=[:,:,5]"

        foo://example.com:8042/over/there?name=ferret#nose
         \_/   \______________/\_________/ \_________/ \__/
          |           |            |            |        |
       scheme     authority       path        query   fragment
    """
    if ":" in fname:
        url = urlparse(fname)
        if url.scheme == "file":
            return os.path.exists(url.path)
        elif url.scheme == "nxs":
            if not os.path.exists(url.path):
                return False
            try:
                nxs = Nexus(url.path)
            except:
                return False
            else:
                return bool(nxs.find_data())
        elif url.scheme == "hdf5":
            if not os.path.exists(url.path):
                return False
            h5 = h5py.File(url.path, "r")
            try:
                dset = h5[url.query]
            except Exception:
                return False
            else:
                return isinstance(dset, h5py.Dataset)

    else:
        return os.path.exists(fname)



def get_isotime(forceTime=None):
    """
    @param forceTime: enforce a given time (current by default)
    @type forceTime: float
    @return: the current time as an ISO8601 string
    @rtype: string
    """
    if forceTime is None:
        forceTime = time.time()
    localtime = time.localtime(forceTime)
    gmtime = time.gmtime(forceTime)
    tz_h = localtime.tm_hour - gmtime.tm_hour
    tz_m = localtime.tm_min - gmtime.tm_min
    return "%s%+03i:%02i" % (time.strftime("%Y-%m-%dT%H:%M:%S", localtime), tz_h, tz_m)


def from_isotime(text, use_tz=False):
    """
    @param text: string representing the time is iso format
    """
    text = str(text)
    base = text[:19]
    if use_tz and len(text) == 25:
        sgn = 1 if  text[:19] == "+" else -1
        tz = 60 * (60 * int(text[20:22]) + int(text[23:25])) * sgn
    else:
        tz = 0
    return time.mktime(time.strptime(base, "%Y-%m-%dT%H:%M:%S")) + tz


def is_hdf5(filename):
    """
    Check if a file is actually a HDF5 file

    @param filename: this file has better to exist
    """
    signature = [137, 72, 68, 70, 13, 10, 26, 10]
    if not os.path.exists(filename):
        raise IOError("No such file %s" % (filename))
    with open(filename, "rb") as f:
        sig = [ord(i) for i in f.read(8)]
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

        @param filename: name of the hdf5 file containing the nexus
        @param mode: can be r or a
        """
        self.filename = os.path.abspath(filename)
        self.mode = mode
        if not h5py:
            logger.error("h5py module missing: NeXus not supported")
            raise RuntimeError("H5py module is missing")
        if os.path.exists(self.filename) and self.mode == "r":
            self.h5 = h5py.File(self.filename, mode=self.mode)
        else:
            self.h5 = h5py.File(self.filename)
        self.to_close = []

    def close(self):
        """
        close the filename and update all entries
        """
        end_time = get_isotime()
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

        @param name: name of the entry to retrieve
        @return: HDF5 group of NXclass == NXentry
        """
        for grp_name in self.h5:
            if  grp_name == name:
                grp = self.h5[grp_name]
                if isinstance(grp, h5py.Group) and \
                    "start_time" in grp and  \
                    "NX_class" in grp.attrs and \
                    grp.attrs["NX_class"] == "NXentry" :
                        return grp

    def get_entries(self):
        """
        retrieves all entry sorted the latest first.

        @return: list of HDF5 groups
        """
        entries = [(grp, from_isotime(self.h5[grp + "/start_time"].value))
                    for grp in self.h5
                    if (isinstance(self.h5[grp], h5py.Group) and \
                        "start_time" in self.h5[grp] and  \
                        "NX_class" in self.h5[grp].attrs and \
                        self.h5[grp].attrs["NX_class"] == "NXentry")]
        if entries :
            entries.sort(key=lambda a: a[1], reverse=True)  # sort entries in decreasing time
            return [self.h5[i[0]] for i in entries]
        else:  # no entries found, try without sorting by time
            entries = [grp for grp in self.h5
                    if (isinstance(self.h5[grp], h5py.Group) and \
                        "NX_class" in self.h5[grp].attrs and \
                        self.h5[grp].attrs["NX_class"] == "NXentry")]
            entries.sort(reverse=True)
            return [self.h5[i] for i in entries]



    def find_detector(self, all=False):
        """
        Tries to find a detector within a NeXus file, takes the first compatible detector

        @param all: return all detectors found as a list
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

        @param all: return all detectors found as a list
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


    def new_entry(self, entry="entry", program_name="pyFAI", title="description of experiment", force_time=None):
        """
        Create a new entry

        @param entry: name of the entry
        @param program_name: value of the field as string
        @param title: value of the field as string
        @force_time: enforce the start_time (as string!)
        @return: the corresponding HDF5 group
        """
        nb_entries = len(self.get_entries())
        entry_grp = self.h5.require_group("%s_%04i" % (entry, nb_entries))
        entry_grp.attrs["NX_class"] = "NXentry"
        entry_grp["title"] = numpy.string_(title)
        entry_grp["program_name"] = numpy.string_(program_name)
        if force_time:
            entry_grp["start_time"] = numpy.string_(force_time)
        else:
            entry_grp["start_time"] = numpy.string_(get_isotime())
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
        @param grp: parent group
        @param name: name of the sub-group
        @param class_type: NeXus class name
        @return: subgroup created
        """
        sub = grp.require_group(name)
        sub.attrs["NX_class"] = class_type
        return sub

    def new_detector(self, name="detector", entry="entry", subentry="pyFAI"):
        """
        Create a new entry/pyFAI/Detector

        @param detector: name of the detector
        @param entry: name of the entry
        @param subentry: all pyFAI description of detectors should be in a pyFAI sub-entry
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

        @param grp: HDF5 group
        @param class_type: name of the NeXus class
        """
        coll = [grp[name] for name in grp
               if (isinstance(grp[name], h5py.Group) and \
                   "NX_class" in grp[name].attrs and \
                   grp[name].attrs["NX_class"] == class_type)]
        return coll

    def get_data(self, grp, class_type="NXdata"):
        """
        return all dataset of the the NeXus class NXdata

        @param grp: HDF5 group
        @param class_type: name of the NeXus class
        """
        result = []
        for grp in self.get_class(grp, class_type):
            result += [grp[name] for name in grp \
               if (isinstance(grp[name], h5py.Dataset) and \
                   ("signal" in grp[name].attrs))]
        return result

    def deep_copy(self, name, obj, where="/", toplevel=None, excluded=None, overwrite=False):
        """
        perform a deep copy:
        create a "name" entry in self containing a copy of the object

        @param where: path to the toplevel object (i.e. root)
        @param  toplevel: firectly the top level Group
        @param excluded: list of keys to be excluded
        @param overwrite: replace content if already existing
        """
        if (excluded is not None) and (name in excluded):
            return
        if not toplevel:
            toplevel = self.h5[where]
        if isinstance(obj, h5py.Group):
            if not name in toplevel:
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

