#!/usr/bin/env python
# coding: utf-8
#
#    Project: X-ray image reader
#             https://github.com/silx-kit/fabio
#
#
#    Copyright (C) European Synchrotron Radiation Facility, Grenoble, France
#
#    Principal author:       Jérôme Kieffer (Jerome.Kieffer@ESRF.eu)
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

"""Portable image converter based on FabIO library
to export Eiger frames (including the one from LImA)
to a set of esperanto frames which can be imported 
into CrysalisPro.
"""

__author__ = "Jerome Kieffer"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__licence__ = "MIT"
__date__ = "23/02/2023"
__status__ = "production"

FOOTER = """To import your files as a project:
* Start CrysalisPro and open any project
* press "F5" to open the console
* Type `esperanto createrunlist` and select your first and last frame
"""

import logging
logging.basicConfig()
logger = logging.getLogger("eiger2crysalis")
import sys
import os
import shutil
from .. import esperantoimage, eigerimage, limaimage, sparseimage, xcaliburimage
from ..openimage import openimage as fabio_open
from .._version import version as fabio_version
from ..nexus import get_isotime
from ..utils.cli import ProgressBar, expand_args
import numpy
import argparse
try:
    import hdf5plugin
except ImportError:
    pass

try:
    import numexpr
except ImportError:
    logger.error("Numexpr is needed to interpret formula ...")

EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EXIT_ARGUMENT_FAILURE = 2

try:
    from scipy import constants
except ImportError:
    # Updated with scipy 1.4
    CONST_hc = 12.398419843320026
else:
    CONST_hc = constants.c * constants.h / constants.e * 1e7


def as_str(smth):
    "Transform to string"
    if isinstance(any, bytes):
        return smth.decode()
    else:
        return str(smth)


class Converter:

    def __init__(self, options):
        self.options = options
        self.mask = None
        if not self.options.verbose:
            self.progress = ProgressBar("HDF5 --> Esperanto", len(options.images), 30)
        self.succeeded = True

        prefix = os.path.commonprefix([os.path.abspath(i) for i in self.options.images])
        if "{dirname}" in self.options.output:
            self.dirname = os.path.dirname(prefix)
        else:
            self.dirname = os.path.dirname(os.path.abspath(self.options.output))
        if "{prefix}" in self.options.output:
            self.prefix = os.path.basename(prefix)+"_1"
        else:
            self.prefix = os.path.basename(os.path.abspath(self.options.output)).split("{")[0]
        self.headers = None
        self.processed_frames = None
        self.scan_type = None
        self.angle_ranges = {}

    def geometry_transform(self, image):
        "Transforms an image according to the requested command line options"
        if self.options.rotation:
            image = numpy.rot90(image, k=self.options.rotation // 90)
        if self.options.transpose:
            image = image.T
        if self.options.flip_ud:
            image = numpy.flipud(image)
        if self.options.flip_lr:
            image = numpy.fliplr(image)
        return image

    def new_beam_center(self, x, y, shape):
        """Calculate the position of the beam after all transformations:
        
        :param x, y: position in the initial image
        :shape: shape of the input image
        :return: x, y, coordinated of the new beam center within the esperanto frame.
        """
        dummy = 123
        m = numpy.zeros(shape, dtype=numpy.int32)
        m[int(y + 0.5), int(x + 0.5)] = dummy

        f = esperantoimage.EsperantoImage(data=m)
        n = self.geometry_transform(f.data)
        w = numpy.argmin(abs(n.ravel() - dummy))
        return w % n.shape[-1], w // n.shape[-1]

    def convert_all(self):
        self.succeeded = True
        self.processed_frames = 0
        self.headers = self.common_headers()
        for filename in self.options.images:
            finish_at = self.convert_one(filename, self.processed_frames)
            self.succeeded = self.succeeded and (finish_at > 0)
            self.processed_frames += finish_at

    def finish(self):
        if not self.succeeded:
            if not self.options.verbose:
                self.progress.clear()
            print("Conversion or part of it failed. You can try with --debug to have more output information.")
            return EXIT_FAILURE
        else:
            if not self.options.verbose:
                self.progress.clear()
            print(FOOTER)
            return EXIT_SUCCESS

    def common_headers(self):
        headers = {
                    # SPECIAL_CCD_1
                    "delectronsperadu": 1,
                    "ldarkcorrectionswitch": 0,
                    "lfloodfieldcorrectionswitch/mode": 0,
                    "dsystemdcdb2gain": 1.0,
                    "ddarksignal": 0,
                    "dreadnoiserms": 0,
                    # SPECIAL_CCD_2
                    "ioverflowflag":0 ,
                    "ioverflowafterremeasureflag":0,
                    "inumofdarkcurrentimages":0,
                    "inumofmultipleimages":0,
                    "loverflowthreshold": 1000000,
                    # SPECIAL_CCD_3
                    # SPECIAL_CCD_4
                    # SPECIAL_CCD_5
                    # TIME
                    # "dexposuretimeinsec": 0.2,
                    "doverflowtimeinsec": 0 ,
                    "doverflowfilter":0,
                    # MONITOR
                    # PIXELSIZE
                    # "drealpixelsizex": 0.075,
                    # "drealpixelsizey": 0.075,
                    "dsithicknessmmforpixeldetector": 1,
                # TIMESTAMP
                "timestampstring": get_isotime(),
                # GRIDPATTERN
                # STARTANGLESINDEG
    #             "dom_s":-180 + i,
    #             "dth_s":0,
    #             "dka_s":0,
    #             "dph_s":0,
                # ENDANGLESINDEG
    #             "dom_e":-179 + i,
    #             "dth_e": 0,
    #             "dka_e": 0,
    #             "dph_e": 0,
                # GONIOMODEL_1
                "dbeam2indeg":0,
                "dbeam3indeg":0,
                "detectorrotindeg_x":0,
                "detectorrotindeg_y":0,
                "detectorrotindeg_z":0,
    #             "dxorigininpix":  img.data.shape[1] - (img.data.shape[1] - data.shape[1]) / 2 - center_x,
    #             "dyorigininpix": img.data.shape[0] - center_y,
                "dalphaindeg": 50,
                "dbetaindeg": 0,
#                 "ddistanceinmm": 117,
                # GONIOMODEL_2
                # WAVELENGTH
                # "dalpha1": wl,
                # "dalpha2": wl,
                # "dalpha12": wl,
                # "dbeta1": wl,
                # MONOCHROMATOR
                "ddvalue-prepolfac": 0.98,
                "orientation-type": "SYNCHROTRON",
                # ABSTORUN
                }

        with fabio_open(self.options.images[0]) as source:
            shape = source.data.shape
            dtype = source.data.dtype
            if self.progress is not None:
                self.progress.max_value = source.nframes * len(self.options.images)
            if isinstance(source, limaimage.LimaImage):
                # Populate the Pilatus header from the Lima
                entry_name = source.h5.attrs.get("default")
                if entry_name:
                    entry = source.h5.get(entry_name)
                    if entry:
                        data_name = entry.attrs["default"]
                        if data_name:
                            data_grp = entry.get(data_name)
                            if data_grp:
                                nxdetector = data_grp.parent
                                try:
                                    headers["drealpixelsizex"] = nxdetector["detector_information/pixel_size/xsize"][()] * 1e3
                                    headers["drealpixelsizey"] = nxdetector["detector_information/pixel_size/ysize"][()] * 1e3
                                except Exception as e:
                                    logger.warning("Error in searching for pixel size (%s): %s", type(e), e)
                                try:
                                    t1 = nxdetector["acquisition/exposure_time"][()]
                                    headers["dexposuretimeinsec"] = t1
                                except Exception as e:
                                    logger.warning("Error in searching for exposure time (%s): %s", type(e), e)
            elif isinstance(source, sparseimage.SparseImage):
                entry_name = source.h5.attrs.get("default")
                if entry_name:
                    entry = source.h5.get(entry_name)
                    if entry:
                        instruments = [i for  i in entry.values() if as_str(i.attrs.get("NX_class", "")) == "NXinstrument"]
                        if instruments:
                            instrument = instruments[0]
                            detectors = [i for  i in instrument.values() if as_str(i.attrs.get("NX_class", "")) == "NXdetector"]
                            if detectors:
                                detector = detectors[0]
                                headers["drealpixelsizex"] = detector["x_pixel_size"][()] * 1e3
                                headers["drealpixelsizey"] = detector["y_pixel_size"][()] * 1e3
                                headers["dxorigininpix"] = detector["beam_center_x"][()]
                                headers["dyorigininpix"] = detector["beam_center_y"][()]
                                headers["ddistanceinmm"] = detector["distance"][()] * 1e3
                            monchromators = [i for  i in instrument.values() if as_str(i.attrs.get("NX_class", "")) == "NXmonochromator"]
                            if monchromators:
                                wavelength = monchromators[0]["wavelength"][()]
                self.mask = numpy.logical_not(numpy.isfinite(source.mask))
                headers["dexposuretimeinsec"] = 1  # meaningfull value.

            elif isinstance(source, eigerimage.EigerImage):
                raise NotImplementedError("Please implement Eiger detector data format parsing or at least open an issue")
            else:
                raise NotImplementedError("Unsupported format: %s" % source.__class__.__name__)
        if self.mask is None:
            self.mask = numpy.zeros(shape, dtype=dtype)
        # Parse option for headers
        if self.options.energy:
            wavelength = CONST_hc / self.options.energy
        elif self.options.wavelength:
            wavelength = self.options.wavelength
        headers["dalpha1"] = headers["dalpha2"] = headers["dalpha12"] = headers["dbeta1"] = wavelength
        if self.options.distance:
            headers["ddistanceinmm"] = self.options.distance
        if self.options.beam:
            x, y = self.options.beam
            x, y = self.new_beam_center(x, y, shape)
            headers["dxorigininpix"] = x
            headers["dyorigininpix"] = y
        if self.options.alpha:
            headers["dalphaindeg"] = self.options.alpha
        if self.options.kappa is not None:
            try:
                value = float(self.options.kappa)
            except ValueError:  # Handle the string
                value = numexpr.NumExpr(self.options.kappa)
                self.scan_type = "kappa"
            headers["dka_s"] = headers["dka_e"] = value
        if self.options.theta is not None:
            try:
                value = float(self.options.theta)
            except ValueError:  # Handle the string
                value = numexpr.NumExpr(self.options.theta)
                self.scan_type = "theta"
            headers["dth_s"] = headers["dth_e"] = value
        if self.options.phi is not None:
            try:
                value = float(self.options.phi)
            except ValueError:  # Handle the string
                value = numexpr.NumExpr(self.options.phi)
                self.scan_type = "phi"
            headers["dph_s"] = headers["dph_e"] = value
        if self.options.omega is not None:
            try:
                value = float(self.options.omega)
            except ValueError:
                # Handle the string
                value = numexpr.NumExpr(self.options.omega)
                self.scan_type = "omega"
            headers["dom_s"] = headers["dom_e"] = value

        return headers

    def convert_one(self, input_filename, start_at=0):
        """
        Convert a single file using options
    
        :param str input_filename: The input filename
        :param object options: List of options provided from the command line
        :param start_at: index to start at for given file
        :rtype: int
        :returns: the number of frames processed
        """
        self.progress.update(start_at + 0.5, input_filename)
        input_filename = os.path.abspath(input_filename)
        input_exists = os.path.exists(input_filename)

        if self.options.verbose:
            print("Converting file '%s'" % (input_filename))

        if not input_exists:
            logger.error("Input file '%s' do not exists. Conversion skipped.", input_filename)
            return -1

        try:
            logger.debug("Load '%s'", input_filename)
            source = fabio_open(input_filename)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            logger.error("Loading input file '%s' failed cause: \"%s\". Conversion skipped.", input_filename, e.message)
            logger.debug("Backtrace", exc_info=True)
            return -1

        for i, frame in enumerate(source):
            idx = i + start_at
            self.progress.update(idx + 0.5, input_filename + " - " + str(idx))
            input_data = frame.data
            numpy.maximum(self.mask, input_data, out=self.mask)
            input_data = input_data.astype(numpy.int32)
            input_data[input_data == numpy.iinfo(frame.data.dtype).max] = self.options.dummy
            converted = esperantoimage.EsperantoImage(data=input_data)  # This changes the shape
            converted.data = self.geometry_transform(converted.data)
            for k, v in self.headers.items():
                if callable(v):
                    if k.endswith("s"):
                        v0 = converted.header[k] = v(idx)
                    else:  # k.endswith("e"):
                        v1 = converted.header[k] = v(idx + 1)
                else:
                    v0 = v1 = converted.header[k] = v
                if k in self.angle_ranges:
                    v = self.angle_ranges[k]
                    self.angle_ranges[k] = (min(v[0], v0, v1), max(v[1], v0, v1))
                else:
                    self.angle_ranges[k] = (min(v0, v1), max(v0, v1))

            output_filename = self.options.output.format(index=((idx + self.options.offset)),
                                                         prefix=self.prefix,
                                                         dirname=self.dirname)
            os.makedirs(os.path.dirname(output_filename), exist_ok=True)
            try:
                logger.debug("Write '%s'", output_filename)
                if not self.options.dry_run:
                    converted.write(output_filename)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                logger.error("Saving output file '%s' failed cause: \"%s: %s\". Conversion skipped.", output_filename, type(e), e)
                logger.debug("Backtrace", exc_info=True)
                return -1
        return source.nframes

    def treat_mask(self, full=False):
        ":param full: complete/slow mask analysis"
        if self.progress:
            self.progress.update(self.progress.max_value - 1, "Generate mask")
        dummy_value = numpy.cast[self.mask.dtype](-1)
        mask = (self.mask==dummy_value).astype(numpy.int8)
        esperantoimage.EsperantoImage.DUMMY = 1
        new_mask = self.geometry_transform(esperantoimage.EsperantoImage(data=mask).data)
        esperantoimage.EsperantoImage.DUMMY = -1 # restore the class !
        if self.progress:
            self.progress.update(self.progress.max_value - 1, f"Decompose mask full={full}")
        xci = xcaliburimage.XcaliburImage(data=new_mask)
        ccd = xci.decompose(full)
        if self.progress:
            self.progress.update(self.progress.max_value - 0.5, "Exporting mask as CCD/SET file")
        dummy_filename = self.options.output.format(index=self.options.offset,
                                                     prefix=self.prefix,
                                                     dirname=self.dirname)
        dirname = os.path.dirname(dummy_filename)
        prefix = self.prefix.split("_")[0]
        numpy.save(os.path.join(dirname, prefix + "_mask.npy"), new_mask)
        ccd.save(os.path.join(dirname, prefix + ".ccd"))
        with open(os.path.join(dirname, prefix + ".set"), mode="wb") as maskfile:
            maskfile.write(b'#XCALIBUR SYSTEM\r\n')
            maskfile.write(b'#XCALIBUR SETUP FILE\r\n')
            maskfile.write(b'#*******************************************************************************************************\r\n')
            maskfile.write(b'# CHIP CHARACTERISTICS e_19_020609.ccd         D A T E Wed-Sep-16-10-00-59-2009\r\n')
            maskfile.write(b'# This program produces version 1.9\r\n')
            maskfile.write(b'#******************************************************************************************************\r\n')
            maskfile.write(b'#THIS FILE IS USER READABLE - BUT SHOULD NOT BE TOUCHED BY THE USER\r\n')
            maskfile.write(b'#ANY CHANGES TO THIS FILE WILL RESULT IN LOSS OF WARRANTY!\r\n')
            maskfile.write(b'#CHIP IDCODE producer type serial\r\n')
            maskfile.write(b'CHIP IDCODE "n/a" "n/a" "n/a\r\n')
            maskfile.write(b'#CHIP TAPER producer type serial\r\n')
            maskfile.write(b'CHIP TAPER "" "" ""\r\n')
            maskfile.write(b'#ALL COORDINATES GO FROM 0 TO N-1\r\n')
            maskfile.write(b'#CHIP BADPOINT treatment options: IGNORE,REPLACE,AVERAGE\r\n')
            maskfile.write(b'#CHIP BADPOINT x1x1 y1x1 treatment r1x1x1 r1y1x1 r2x1x1 r2y1x1\r\n')
            maskfile.write(b'#CHIP BADPOINT 630 422 REPLACE 632 422 0 0\r\n')
            maskfile.write(b'#CHIP BADRECTANGLE xl xr yb yt\r\n')
            for r in ccd.pschipbadpolygon:
                    maskfile.write(f"CHIP BADRECTANGLE {r.iax[0]} {r.iax[1]} {r.iay[0]} {r.iay[1]}\r\n".encode())
            for r in ccd.pschipbadpoint:
                    maskfile.write(f"CHIP BADPOINT {r.spt.ix} {r.spt.iy} IGNORE {r.spt.ix} {r.spt.iy} {r.spt.ix} {r.spt.iy}\r\n".encode())
            maskfile.write(b'#END OF XCALIBUR CHIP CHARACTERISTICS FILE\r\n')
        # Make a backup as the original could be overwritten by Crysalis at import
        shutil.copyfile(os.path.join(dirname, prefix + ".set"), os.path.join(dirname, prefix + ".set.orig"))
        
        # save the ".run" file
        rundescription = xcaliburimage.RunDescription(prefix, dirname, pssweep=[])
        if self.scan_type=="phi":
            iscantype = xcaliburimage.SCAN_TYPE.Phi.value
            dstart = self.headers["dph_s"](0)
            dend = self.headers["dph_s"](self.processed_frames)
            dphi = 0.0
            domega = self.headers["dom_s"]
        else: #Omega-scan
            iscantype = xcaliburimage.SCAN_TYPE.Omega.value
            dstart = self.headers["dom_s"](0)
            dend = self.headers["dom_s"](self.processed_frames)
            dphi = self.headers["dph_s"]
            domega = 0.0
            
        oscil = (dend-dstart)/self.processed_frames
        sweep = xcaliburimage.Sweep(0,
                                    iscantype,
                                    domega=domega,
                                    dtheta=self.headers["dth_s"],
                                    dkappa=self.headers["dka_s"],
                                    dphi=dphi,
                                    dstart=dstart, dend=dend,
                                    dwidth=oscil,
                                    dunknown2=0.0, 
                                    iunknown3=self.processed_frames, 
                                    iunknown4=0, 
                                    iunknown5=self.processed_frames, iunknown6=0,
                                    dexposure=self.headers["dexposuretimeinsec"]
                                    )
        rundescription.pssweep.append(sweep)
        rundescription.save(os.path.join(dirname,prefix+".run"))

        # Finally save the ".par" file
        xci.save_par(dirname, prefix, 
                     wavelength=self.options.wavelength,
                     alpha=self.options.alpha,
                     polarization=self.options.polarization,
                     distance=self.options.distance,
                     oscil=oscil,
                     center_x=self.headers["dxorigininpix"],
                     center_y=self.headers["dyorigininpix"]
                     )


def main():

    epilog = """return codes: 0 means a success. 1 means the conversion
                contains a failure, 2 means there was an error in the
                arguments"""

    parser = argparse.ArgumentParser(prog="eiger2crysalis",
                                     description=__doc__,
                                     epilog=epilog)
    parser.add_argument("IMAGE", nargs="*",
                        help="File with input images")
    parser.add_argument("-V", "--version", action='version', version=fabio_version,
                        help="output version and exit")
    parser.add_argument("-v", "--verbose", action='store_true', dest="verbose", default=False,
                        help="show information for each conversions")
    parser.add_argument("--debug", action='store_true', dest="debug", default=False,
                        help="show debug information")
    group = parser.add_argument_group("main arguments")
    group.add_argument("-l", "--list", action="store_true", dest="list", default=None,
                       help="show the list of available formats and exit")
    group.add_argument("-o", "--output", default='{dirname}/{prefix}/{prefix}_1_{index}.esperanto', type=str,
                       help="output directory and filename template")
    group.add_argument("-O", "--offset", type=int, default=1,
                       help="index offset, CrysalisPro likes indexes to start at 1, Python starts at 0")
    group.add_argument("-D", "--dummy", type=int, default=-1,
                       help="Set masked values to this dummy value")

    group = parser.add_argument_group("optional behaviour arguments")
#     group.add_argument("-f", "--force", dest="force", action="store_true", default=False,
#                        help="if an existing destination file cannot be" +
#                        " opened, remove it and try again (this option" +
#                        " is ignored when the -n option is also used)")
#     group.add_argument("-n", "--no-clobber", dest="no_clobber", action="store_true", default=False,
#                        help="do not overwrite an existing file (this option" +
#                        " is ignored when the -i option is also used)")
#     group.add_argument("--remove-destination", dest="remove_destination", action="store_true", default=False,
#                        help="remove each existing destination file before" +
#                        " attempting to open it (contrast with --force)")
#     group.add_argument("-u", "--update", dest="update", action="store_true", default=False,
#                        help="copy only when the SOURCE file is newer" +
#                        " than the destination file or when the" +
#                        " destination file is missing")
#     group.add_argument("-i", "--interactive", dest="interactive", action="store_true", default=False,
#                        help="prompt before overwrite (overrides a previous -n" +
#                        " option)")
    group.add_argument("--dry-run", dest="dry_run", action="store_true", default=False,
                       help="do everything except modifying the file system")
    group.add_argument("--calc-mask", dest="calc_mask", default=False, action="store_true",
                       help="Generate a fine mask from pixels marked as invalid. By default, only treats gaps")

    group = parser.add_argument_group("Experimental setup options")
    group.add_argument("-e", "--energy", type=float, default=None,
                       help="Energy of the incident beam in keV")
    group.add_argument("-w", "--wavelength", type=float, default=None,
                       help="Wavelength of the incident beam in Å")
    group.add_argument("-d", "--distance", type=float, default=None,
                       help="Detector distance in millimeters")
    group.add_argument("-b", "--beam", nargs=2, type=float, default=None,
                       help="Direct beam in pixels x, y")
    group.add_argument("-p", "--polarization", type=float, default=0.99,
                       help="Polarization factor (0.99 by default on synchrotron)")

    group = parser.add_argument_group("Goniometer setup")
#     group.add_argument("--axis", type=str, default=None,
#                        help="Goniometer angle used for scanning: 'omega', 'phi' or 'kappa'")
    group.add_argument("--alpha", type=float, default=50,
                       help="Goniometer angle alpha value in deg. Constant, angle between kappa/omega.")
    group.add_argument("--kappa", type=str, default=0,
                       help="Goniometer angle kappa value in deg or formula f(index).")
#     group.add_argument("--chi", type=str, default=0,
#                        help="Goniometer angle chi value in deg. or formula f(index).")
    group.add_argument("--phi", type=str, default=0,
                       help="Goniometer angle phi value in deg. or formula f(index). Inner-most rotation.")
    group.add_argument("--omega", type=str, default=0,
                       help="Goniometer angle omega value in deg. or formula f(index). Outer-most rotation.")
    group.add_argument("--theta", type=str, default=0,
                       help="Goniometer angle theta value in deg. or formula f(index). Tilt angle of the detector.")

    group = parser.add_argument_group("Image preprocessing (Important: applied in this order!)")
    group.add_argument("--rotation", type=int, default=180,
                       help="Rotate the initial image by this value in degrees. Must be a multiple of 90°. By default 180 deg (flip_up with origin=lower and flip_lr because the image is seen from the sample).")
    group.add_argument("--transpose", default=False, action="store_true",
                       help="Flip the x/y axis")
    group.add_argument("--flip-ud", dest="flip_ud", default=False, action="store_true",
                       help="Flip the image upside-down")
    group.add_argument("--flip-lr", dest="flip_lr", default=False, action="store_true",
                       help="Flip the image left-right")

    try:
        args = parser.parse_args()

        if args.debug:
            logger.setLevel(logging.DEBUG)

        if args.list:
            print("Supported formats: LimaImage, EigerImage, SparseImage")
            return

        if len(args.IMAGE) == 0:
            raise argparse.ArgumentError(None, "No input file specified.")

        # the upper case IMAGE is used for the --help auto-documentation
        args.images = expand_args(args.IMAGE)
        args.images.sort()
    except argparse.ArgumentError as e:
        logger.error(e.message)
        logger.debug("Backtrace", exc_info=True)
        return EXIT_ARGUMENT_FAILURE
    esperantoimage.EsperantoImage.DUMMY = args.dummy
    converter = Converter(args)
    converter.convert_all()
    converter.treat_mask(full=args.calc_mask)
    return converter.finish()


if __name__ == "__main__":
    result = main()
    sys.exit(result)
