#!/usr/bin/env python

__date__ = "10/07/2024"
__author__ = "Jerome Kieffer"
__license__ = "MIT"

import os
import sys
import argparse
import logging
application_name = os.path.splitext(os.path.basename(__file__))[0]
logger = logging.getLogger(application_name)
logging.basicConfig()
import numpy
import fabio
from fabio.nexus import Nexus
import h5py
import hdf5plugin
try:
    from pyFAI import load
except ImportError:
    pyFAI = None
    logger.error("Unable to import pyFAI, won't be able to parse PONI-file!")


def parse(argv=None):
    if argv is None:
        argv = []
    parser = argparse.ArgumentParser(prog=application_name,
                    description='Convert any HDF5 file containing images to a file processable by XDS using the neggia plugin from Dectris.'
                                 'Do not forget to specify LIB=/path/to/plugin/dectris-neggia.so in XDS.INP',
                    epilog='Requires hdf5plugin and pyFAI to parse configuration file. Geometry can be calibrated with pyFAI-calib2')
    parser.add_argument("input", nargs='+',  help="Space separated list of input files (HDF5)")
    parser.add_argument("--verbose", "-v", help="increase output verbosity",
                        action="count")
    parser.add_argument("--force", "-f", help="force overwrite output file",
                        action="store_true")
    parser.add_argument("--copy", "-c", help="copy dataset instead of using external links",
                        action="store_true")
    parser.add_argument("--geometry", "-g", help="PONI-file containing the geometry (pyFAI format, MANDATORY)")
    parser.add_argument("--output", "-o", help="output filename", default="master.h5")
    return parser.parse_args(argv)

def process(options):
    if options.verbose:
        if options.verbose>1:
            logger.setLevel(logging.debug)
        else:
            logger.setLevel(logging.info)

    if not options.geometry or not os.path.exists(options.geometry):
        logger.error("Unable to parse PONI-file: %s", options.geometry)
        return 1
    try:
        poni = load(options.geometry)
    except Exception as err:
        logger.error("Unable to parse PONI-file: %s", options.geometry)
        raise err
        return 1
    f2d = poni.getFit2D()
    
    if len(options.input)==0:
        logger.error("No input HDF5 file provided. Aborting")
        return 1
    frames = [fabio.open(i) for i in options.input]
    if os.path.exists(options.output):
        if options.force:
            mode = "w"
        else:
            logger.error("Output file exist, not overwriting it. Aborting")
            return 1
    else:
        mode = "w"

    dest_dir = os.path.dirname(os.path.abspath(options.output))
    with Nexus(options.output, mode) as nxs:
        entry = nxs.new_entry(entry="entry", program_name=application_name, force_name=True)
        instrument = nxs.new_instrument(entry=entry, instrument_name="instrument")
        if poni.wavelength:
            beam = nxs.new_class(instrument, "beam", "NXbeam")
            beam.create_dataset("incident_wavelength", data=poni.wavelength*1e10).attrs["unit"] = "A"
        detector = nxs.new_class(instrument, "detector", "NXdetector")
        detector.create_dataset("x_pixel_size", data=float(poni.pixel2)).attrs["unit"] = "m"
        detector.create_dataset("y_pixel_size", data=float(poni.pixel1)).attrs["unit"] = "m"
        detector.create_dataset("beam_center_x", data=float(f2d["centerX"])).attrs["unit"] = "pixel"
        detector.create_dataset("beam_center_y", data=float(f2d["centerY"])).attrs["unit"] = "pixel"
        detector.create_dataset("detector_distance", data=f2d["directDist"]*1e-3).attrs["unit"] = "m"
        detectorSpecific = nxs.new_class(detector, "detectorSpecific", "NXcollection")
        detectorSpecific.create_dataset("nimages", data=sum(i.nframes for i in frames))
        detectorSpecific.create_dataset("ntrigger", data=1)
        mask = poni.detector.mask
        if mask is None:
            mask = numpy.zeros(poni.detector.shape, dtype="uint32")
        else:
            mask = mask.astype("uint32")
        detectorSpecific.create_dataset("pixel_mask", data=mask)
        data = nxs.new_class(entry, "data", "NXdata")
        cnt = 0
        for fimg in frames:
            if isinstance(fimg.dataset, h5py.Dataset):
                cnt += 1
                if options.copy:
                    data.create_dataset(f"data_{cnt:06d}", data=fimg.dataset[()],
                                        chunks=(1,)+fimg.shape,
                                        **hdf5plugin.Bitshuffle(nelems=0, cname='lz4'))
                else:
                    data[f"data_{cnt:06d}"] = h5py.ExternalLink(os.path.relpath(fimg.dataset.file.filename, dest_dir), fimg.dataset.name)
            elif isinstance(fimg.dataset, numpy.ndarray):
                cnt += 1
                if fimg.dataset.ndim < 3:
                    dataset = numpy.atleast_3d(fimg.dataset)
                    dataset.shape = (1,)*(3-fimg.dataset.ndim)+fimg.dataset.shape
                else:
                    dataset = fimg.dataset
                data.create_dataset(f"data_{cnt:06d}", data=dataset,
                                    chunks=(1,)+fimg.shape,
                                    **hdf5plugin.Bitshuffle(nelems=0, cname='lz4'))
            else: # assume it is a list
                for item in fimg.dataset:
                    # each item can be either a dataset or a numpy array
                    if isinstance(item, h5py.Dataset):
                        cnt += 1
                        if options.copy:
                            data.create_dataset(f"data_{cnt:06d}", data=item[()],
                                                chunks=(1,)+fimg.shape,
                                                **hdf5plugin.Bitshuffle(nelems=0, cname='lz4'))
                        else:
                            data[f"data_{cnt:06d}"] = h5py.ExternalLink(os.path.relpath(item.file.filename, dest_dir), item.name)

                    elif isinstance(fimg.dataset, numpy.ndarray):
                        cnt += 1
                        if fimg.dataset.ndim < 3:
                            dataset = numpy.atleast_3d(item)
                            dataset.shape = (1,)*(3-item.ndim)+item.shape
                        else:
                            dataset = item
                        data.create_dataset(f"data_{cnt:06d}", data=dataset,
                                            chunks=(1,)+fimg.shape,
                                            **hdf5plugin.Bitshuffle(nelems=0, cname='lz4'))
                    else:
                        logger.warning("Don't know how to handle %s, skipping", item)
    return 0


def main():
    options = parse(sys.argv[1:])
    return process(options)


if __name__=="__main__":
    sys.exit(main())
