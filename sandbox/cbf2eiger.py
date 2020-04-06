#!/usr/bin/env python
# -*- coding: utf-8 -*-
#########################################
# Command line converter a bunch of files from CBF to eiger
# European Synchrotron Radiation Facility
#
#########################################
"""Converter a bunch of files from any format to an eiger-data
"""

__author__ = "Jérôme Kieffer"
__copyright__ = "2016 ESRF"
__date__ = "06/04/2020"
__licence__ = "MIT"

import logging
logging.basicConfig()

import os

import numpy
import fabio
from fabio import nexus

import argparse
from threading import Thread, Event

from queue import Queue

logger = logging.getLogger("to_eiger")


class Reader(Thread):
    """Reader with input and output queue 
    """

    def __init__(self, queue_in, queue_out, quit_event):
        """Constructor of the class
        
        :param queue_in: input queue with (index, filename to read) as input
        :param queue_out: output queue with (index, FabioImage) as output
        :param quit_event: the event which tells the thread to end 
        """
        Thread.__init__(self)
        self._queue_in = queue_in
        self._queue_out = queue_out
        self._quit_event = quit_event

    def run(self):
        while not self._quit_event.is_set():
            plop = self._queue_in.get()
            if plop is None:
                break
            idx, fname = plop
            try:
                fimg = fabio.open(fname)
            except Exception as err:
                logger.error(err)
                fimg = None
            self._queue_out.put((idx, fimg))
            self._queue_in.task_done()

    @classmethod
    def build_pool(cls, args, size=1):
        """Create a pool of worker of a given size. 
        
        :param worker: class of the worker (deriving  from Thread) 
        :param args: arguments to be passed to each of the worker
        :param size: size of the pool
        :return: a list of worker 
        """
        workers = []
        for _ in range(size):
            w = cls(*args)
            w.start()
            workers.append(w)
        return workers


def save_eiger(input_files, output_file, filter_=None, nbthreads=None):
    """Save a bunch of files in Eiger-like format
    
    :param input_files: list of input files
    :param output_file: name of the HDF5 file
    :param filter_: Type of compression filter: "gzip", "lz4" or "bitshuffle"
    :param nbthreads: number of parallel reader threads  
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

    if nbthreads:
        queue_in = Queue()
        queue_out = Queue()
        quit_event = Event()
        pool = Reader.build_pool((queue_in, queue_out, quit_event), nbthreads)
        for idx, fname in enumerate(input_files[1:]):
            queue_in.put((idx, fname))
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
        if nbthreads:
            for _ in range(len(input_files) - 1):
                idx, fimg = queue_out.get()
                if fimg.data is None:
                    logger.error("Failed reading file: %s", input_files[idx + 1])
                    continue
                ds[idx + 1] = fimg.data
                queue_out.task_done()

            queue_in.join()
            queue_out.join()
        else:  # don't use the pool of readers
            for idx, fname in enumerate(input_files[1:]):
                ds[idx + 1] = fabio.open(fname).data

    if nbthreads:  # clean up
        quit_event.set()
        for _ in pool:
            queue_in.put(None)


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
    group.add_argument("-n", "--nbthreads", dest='nbthreads', type=int, default=None,
                       help="Numbre of reader threads in parallel")

    opts = parser.parse_args()
    input_files = [os.path.abspath(i) for i in opts.IMAGE if os.path.exists(i)]
    input_files.sort()
    save_eiger(input_files, opts.output, filter_=opts.filter, nbthreads=opts.nbthreads)
