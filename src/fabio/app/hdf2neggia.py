#!/usr/bin/env python

__date__ = "01/10/2024"
__author__ = "Jérôme Kieffer"
__license__ = "MIT"

import os
import sys
import argparse
from io import StringIO
import logging
application_name = os.path.splitext(os.path.basename(__file__))[0]
logger = logging.getLogger(application_name)
logging.basicConfig()
import numpy
from .. import version as fabio_version, date as fabio_date
from ..openimage import openimage as fabio_open
from ..nexus import Nexus
import h5py
import hdf5plugin
try:
    from pyFAI import load
except ImportError:
    pyFAI = None
    logger.error("Unable to import pyFAI, won't be able to parse PONI-file!")




class XDSbuilder:
    def __init__(self):
        "Constructor of the class"
        
        self.poni = None
        self.options = None
        self.frames = None 

    def parse(self, argv=None):
        "Parse command line arguments and return "
        if argv is None:
            argv = []
        parser = argparse.ArgumentParser(prog=application_name,
                        description='Convert any HDF5 file containing images to a file processable by XDS using the neggia plugin from Dectris.'
                                     'Do not forget to specify LIB=/path/to/plugin/dectris-neggia.so in XDS.INP',
                        epilog='Requires hdf5plugin and pyFAI to parse configuration file. Geometry can be calibrated with pyFAI-calib2',)
        parser.add_argument('--version', action='version', version=f'%(prog)s {fabio_version} from {fabio_date}')
        parser.add_argument("input", nargs='+',  help="Space separated list of input files (HDF5)")
        parser.add_argument("--verbose", "-v", help="increase output verbosity",
                            action="count")
        parser.add_argument("--force", "-f", help="force overwrite output file",
                            action="store_true")
        parser.add_argument("--copy", "-c", help="copy dataset instead of using external links",
                            action="store_true")
        parser.add_argument("--geometry", "-g", help="PONI-file containing the geometry (pyFAI format, MANDATORY)")
        parser.add_argument("--output", "-o", help="output filename", default="master.h5")
        parser.add_argument("--CdTe", help="The detector is made of CdTe", default=False, action="store_true")
        self.options = parser.parse_args(argv)
        return self.options
        
    def configure_verboseness(self):
        if self.options and self.options.verbose:
            if self.options.verbose>1:
                logger.setLevel(logging.debug)
            else:
                logger.setLevel(logging.info)
        
    def load_poni(self):
        "return 1 if poni-file cannot be found"
        if self.options is None:
            return 1
        if not self.options.geometry or not os.path.exists(self.options.geometry):
            logger.error("Unable to parse PONI-file: %s", self.options.geometry)
            return 1
        try:
            self.poni = load(self.options.geometry)
        except Exception as err:
            logger.error("Unable to parse PONI-file: %s", self.options.geometry)
            raise err
            return 1
        
    def load_input(self):
        if len(self.options.input)==0:
            logger.error("No input HDF5 file provided. Aborting")
            return 2
        self.frames = [fabio_open(i) for i in self.options.input]
        return 0
        
    def build_neggia(self):
        """Build the neggia file, i.e. the HDF5 file with data + metadata for analysis""" 
        if os.path.exists(self.options.output):
            if self.options.force:
                mode = "w"
            else:
                logger.error("Output file exist, not overwriting it. Aborting")
                return 1
        else:
            mode = "w"
        f2d = self.poni.getFit2D()
        dest_dir = os.path.dirname(os.path.abspath(self.options.output))
        with Nexus(self.options.output, mode) as nxs:
            entry = nxs.new_entry(entry="entry", program_name=application_name, force_name=True)
            instrument = nxs.new_instrument(entry=entry, instrument_name="instrument")
            if self.poni.wavelength:
                beam = nxs.new_class(instrument, "beam", "NXbeam")
                beam.create_dataset("incident_wavelength", data=self.poni.wavelength*1e10).attrs["unit"] = "A"
            detector = nxs.new_class(instrument, "detector", "NXdetector")
            detector.create_dataset("x_pixel_size", data=float(self.poni.pixel2)).attrs["unit"] = "m"
            detector.create_dataset("y_pixel_size", data=float(self.poni.pixel1)).attrs["unit"] = "m"
            detector.create_dataset("beam_center_x", data=float(f2d["centerX"])).attrs["unit"] = "pixel"
            detector.create_dataset("beam_center_y", data=float(f2d["centerY"])).attrs["unit"] = "pixel"
            detector.create_dataset("detector_distance", data=f2d["directDist"]*1e-3).attrs["unit"] = "m"
            detectorSpecific = nxs.new_class(detector, "detectorSpecific", "NXcollection")
            detectorSpecific.create_dataset("nimages", data=sum(i.nframes for i in self.frames))
            detectorSpecific.create_dataset("ntrigger", data=1)
            mask = self.poni.detector.mask
            if mask is None:
                mask = numpy.zeros(self.poni.detector.shape, dtype="uint32")
            else:
                mask = mask.astype("uint32")
            detectorSpecific.create_dataset("pixel_mask", data=mask)
            data = nxs.new_class(entry, "data", "NXdata")
            cnt = 0
            for fimg in self.frames:
                if isinstance(fimg.dataset, h5py.Dataset):
                    cnt += 1
                    if self.options.copy:
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
                            if self.options.copy:
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
    
    def build_XDS(self):
        "Create XDS.INP file suitable for data reduction"
        xds = ["JOB= XYCORR INIT COLSPOT IDXREF DEFPIX INTEGRATE CORRECT",
               "! JOB=  DEFPIX INTEGRATE CORRECT",
               "LIB=./dectris-neggia.so",
               "SPACE_GROUP_NUMBER=0 ! 0 if unknown",
               "FRIEDEL'S_LAW=FALSE     ! This acts only on the CORRECT step",
               "FRACTION_OF_POLARIZATION=0.99",
               "POLARIZATION_PLANE_NORMAL=0 1 0",
               "DIRECTION_OF_DETECTOR_X-AXIS=1 0 0",
               "DIRECTION_OF_DETECTOR_Y-AXIS=0 1 0",
               "INCIDENT_BEAM_DIRECTION=0 0 1",
               "OSCILLATION_RANGE= 0.5",
               ]
        #DATA_RANGE=
        
        shape = self.poni.detector.shape
        pixel1, pixel2 = self.poni.detector.pixel1, self.poni.detector.pixel2
        xds.append(f"NX= {shape[1]:d} NY= {shape[0]:d}  QX= {pixel2*1000:f}  QY= {pixel1*1000:f}")
        
        f2d = self.poni.getFit2D()
        xds.append(f"DETECTOR_DISTANCE= {f2d['directDist']:f}")
        xds.append(f"ORGX= {f2d['centerX']:f} ORGY= {f2d['centerY']:f}")
        
        mask = self.poni.detector.mask
        empty_lines = numpy.where(numpy.std(mask, axis=0) == 0)[0]
        #TODO
        
        #UNTRUSTED_RECTANGLE= 487  495    0 1680
        
        if self.option.CdTe:
            xds.append("SENSOR_THICKNESS=0.75 !mm")
            nrj = self.poni.energy
            e,mu = numpy.loadtxt(StringIO(Attenuations_CdTe),unpack=True)
            xds.append(f"SILICON={numpy.interp(nrj, e, mu)}!1/mm"
        if self.options.outfile:
            outfile = os.path.join(os.path.dirname(os.path.abspath(self.options.outfile)), 
                                   "XDS.INP")
            with open(outfile, "w") as w:
                w.write(os.linesep.join(xds))
        return 0

    def process(self):
        "pipeline processing, returns a error code as integer"
        self.configure_verboseness()
        
        rc = self.load_poni()
        if rc: return rc
        
        rc = self.load_input()
        if rc: return rc
        
        rc = self.build_neggia()
        if rc: return rc
        rc = self.build_XDS()
        if rc: return rc    
        return rc
    
    
def main(argv=None):
    xds = XDSbuilder()
    xds.parse(sys.argv[1:] if argv is None else argv)
    return xds.process()


if __name__=="__main__":
    sys.exit(main())


Attenuations_CdTe = """# E(keV)    µ(1/mm)
  5    4.8824e+02
  6    3.0683e+02
  7    2.0446e+02
  8    1.4391e+02
  9    1.0501e+02
 10    7.9268e+01
 11    6.1074e+01
 12    4.8186e+01
 13    3.8739e+01
 14    3.1654e+01
 15    2.6231e+01
 16    2.1938e+01
 17    1.8545e+01
 18    1.5830e+01
 19    1.3636e+01
 20    1.1835e+01
 21    1.0319e+01
 22    9.0617e+00
 23    8.0028e+00
 24    7.1078e+00
 25    6.3414e+00
 26    5.6880e+00
 27    1.6275e+01
 28    1.4806e+01
 29    1.3508e+01
 30    1.2367e+01
 31    1.1343e+01
 32    1.9767e+01
 33    1.8252e+01
 34    1.6895e+01
 35    1.5666e+01
 36    1.4555e+01
 37    1.3549e+01
 38    1.2630e+01
 39    1.1794e+01
 40    1.1027e+01
 41    1.0331e+01
 42    9.6876e+00
 43    9.0968e+00
 44    8.5527e+00
 45    8.0496e+00
 46    7.5875e+00
 47    7.1604e+00
 48    6.7626e+00
 49    6.3940e+00
 50    6.0547e+00
 51    5.7383e+00
 52    5.4440e+00
 53    5.1696e+00
 54    4.9140e+00
 55    4.6753e+00
 56    4.4518e+00
 57    4.2424e+00
 58    4.0464e+00
 59    3.8622e+00
 60    3.6896e+00
 61    3.5270e+00
 62    3.3737e+00
 63    3.2298e+00
 64    3.0935e+00
 65    2.9654e+00
 66    2.8443e+00
 67    2.7296e+00
 68    2.6214e+00
 69    2.5184e+00
 70    2.4213e+00
 71    2.3295e+00
 72    2.2423e+00
 73    2.1592e+00
 74    2.0803e+00
 75    2.0054e+00
 76    1.9340e+00
 77    1.8662e+00
 78    1.8018e+00
 79    1.7404e+00
 80    1.6819e+00
 81    1.6257e+00
 82    1.5725e+00
 83    1.5210e+00
 84    1.4724e+00
 85    1.4262e+00
 86    1.3812e+00
 87    1.3391e+00
 88    1.2981e+00
 89    1.2589e+00
 90    1.2215e+00
 91    1.1858e+00
 92    1.1513e+00
 93    1.1179e+00
 94    1.0863e+00
 95    1.0559e+00
 96    1.0267e+00
 97    9.9859e-01
 98    9.7168e-01
 99    9.4536e-01
100    9.2021e-01
"""
