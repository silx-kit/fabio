#!/usr/bin/env python
# -*- coding: utf-8 -*-
#########################################
# Command line converter a bunch of files from CBF to eiger
# European Synchrotron Radiation Facility
#
#########################################
"""Converter a bunch of files from any format to an eiger-data
"""

from __future__ import with_statement, print_function

__author__ = u"Jérôme Kieffer"
__copyright__ = "2016 ESRF"
__date__ = "25/11/2016"
__licence__ = "MIT"

import logging
logging.basicConfig()

import sys
import os
import time
import glob

import numpy
import fabio
from fabio import nexus
import h5py

try:
    from fabio.third_party import six
except ImportError:
    import six

try:
    import argparse
except ImportError:
    from fabio.third_party import argparse


from threading import Thread, Event

try:
    from queue import Queue
except:
    from Queue import Queue


logger = logging.getLogger("to_eiger")


def save_eiger(input_files, output_file, filter_=None):
    """Save a bunch of files in Eiger-like format
    
    :param input_files: list of input files
    :param output_file: name of the HDF5 file
    :param filter_: Type of compression filter: "gzip", "lz4" or " 
    """
    assert len(input_files), "Input file list is not empty"
    first_image = input_files[0]
    fimg = fabio.open(first_image)
    shape = fimg.data.shape
    stack_shape = (len(input_files),) + shape
    first_frame_timestamp = os.stat(first_image).st_ctime
    kwfilter = {}
    if filter_ == "gzip":
        kwfilter = {"compression": "gzip", "shuffle": True}
    elif filter_ == "lz4":
        kwfilter = {"compression": 32004, "shuffle": True}
    elif filter_ == "bitshuffle":
        kwfilter = {"compression": 32008, "compression_opts": (0, 2)}  # enforce lz4 compression

    with nexus.Nexus(output_file) as nxs:
        entry = nxs.new_entry(entry='entry', program_name='fabio',
                              title='converted from single-frame files',
                              force_time=first_frame_timestamp,
                              force_name=True)
        data = nxs.new_class(grp=entry, name="data", class_type="NXdata")
        try:
            ds = data.require_dataset(name="data", shape=stack_shape,
                                      dtype=fimg.data.dtype,
                                      chunks=(1,) + shape,
                                      **kwfilter)
        except Exception as error:
            logger.error("Error in creating dataset, disabling compression:%s", error)
            ds = data.require_dataset(name="data", shape=stack_shape,
                                      dtype=fimg.data.dtype,
                                      chunks=(1,) + shape)

        ds[0] = fimg.data
        data["sources"] = [numpy.string_(i) for i in input_files]
        for idx, fname in enumerate(input_files[1:]):
            ds[idx + 1] = fabio.open(fname).data


if __name__ == "__main__":
    epilog = "plop"
    parser = argparse.ArgumentParser(prog="cbf2eiger",
                                     description=__doc__,
                                     epilog=epilog)
    parser.add_argument("IMAGE", nargs="*",
                        help="Input file images")
    parser.add_argument("-V", "--version", action='version', version=fabio.version,
                        help="output version and exit")
    parser.add_argument("-v", "--verbose", action='store_true', dest="verbose", default=False,
                        help="show information for each conversions")
    parser.add_argument("--debug", action='store_true', dest="debug", default=False,
                        help="show debug information")

    group = parser.add_argument_group("main arguments")
    group.add_argument("-l", "--list", action="store_true", dest="list", default=None,
                       help="show the list of available formats and exit")
    group.add_argument("-o", "--output", dest='output', type=str,
                       help="output file or directory")
    group.add_argument("-f", "--filter", dest='filter', type=str, default=None,
                       help="Compression filter, may be lz4, bitshuffle or gzip")
    opts = parser.parse_args()
    save_eiger(opts.IMAGE, opts.output, filter_=opts.filter)
