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
to export Eiger frames (including te one from LIMA)
to CBF and mimic the header from Dectris Pilatus.
"""

__author__ = "Jerome Kieffer"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__licence__ = "MIT"
__date__ = "03/12/2021"
__status__ = "production"

import logging
logging.basicConfig()
logger = logging.getLogger("eiger2cbf")
import codecs
import sys
import os

from ..utils.cli import expand_args
from ..openimage import openimage as fabio_open
from .. import cbfimage, limaimage, eigerimage, version as fabio_version
import numpy
import argparse
try:
    import hdf5plugin
except ImportError:
    pass

try:
    import numexpr
except:
    logger.error("Numexpr is needed to interpret formula ...")

logger = logging.getLogger("eiger2cbf")
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


class ProgressBar:
    """
    Progress bar in shell mode
    """

    def __init__(self, title, max_value, bar_width):
        """
        Create a progress bar using a title, a maximum value and a graphical size.

        The display is done with stdout using carriage return to to hide the
        previous progress. It is not possible to use stdout for something else
        whill a progress bar is in use.

        The result looks like:

        .. code-block:: none

            Title [■■■■■■      ]  50%  Message

        :param str title: Title displayed before the progress bar
        :param float max_value: The maximum value of the progress bar
        :param int bar_width: Size of the progressbar in the screen
        """
        self.title = title
        self.max_value = max_value
        self.bar_width = bar_width
        self.last_size = 0
        self._message = ""
        self._value = 0.0

        encoding = None
        if hasattr(sys.stdout, "encoding"):
            # sys.stdout.encoding can't be used in unittest context with some
            # configurations of TestRunner. It does not exists in Python2
            # StringIO and is None in Python3 StringIO.
            encoding = sys.stdout.encoding
        if encoding is None:
            # We uses the safer aproch: a valid ASCII character.
            self.progress_char = '#'
        else:
            try:
                import datetime
                if str(datetime.datetime.now())[5:10] == "02-14":
                    self.progress_char = u'\u2665'
                else:
                    self.progress_char = u'\u25A0'
                _byte = codecs.encode(self.progress_char, encoding)
            except (ValueError, TypeError, LookupError):
                # In case the char is not supported by the encoding,
                # or if the encoding does not exists
                self.progress_char = '#'

    def clear(self):
        """
        Remove the progress bar from the display and move the cursor
        at the beginning of the line using carriage return.
        """
        sys.stdout.write('\r' + " " * self.last_size + "\r")
        sys.stdout.flush()

    def display(self):
        """
        Display the progress bar to stdout
        """
        self.update(self._value, self._message)

    def update(self, value, message="", max_value=None):
        """
        Update the progrss bar with the progress bar's current value.

        Set the progress bar's current value, compute the percentage
        of progress and update the screen with. Carriage return is used
        first and then the content of the progress bar. The cursor is
        at the begining of the line.

        :param float value: progress bar's current value
        :param str message: message displayed after the progress bar
        :param float max_value: If not none, update the maximum value of the
            progress bar
        """
        if max_value is not None:
            self.max_value = max_value
        self._message = message
        self._value = value

        if self.max_value == 0:
            coef = 1.0
        else:
            coef = (1.0 * value) / self.max_value
        percent = round(coef * 100)
        bar_position = int(coef * self.bar_width)
        if bar_position > self.bar_width:
            bar_position = self.bar_width

        # line to display
        line = '\r%15s [%s%s] % 3d%%  %s' % (self.title, self.progress_char * bar_position, ' ' * (self.bar_width - bar_position), percent, message)

        # trailing to mask the previous message
        line_size = len(line)
        clean_size = self.last_size - line_size
        if clean_size < 0:
            clean_size = 0
        self.last_size = line_size

        sys.stdout.write(line + " " * clean_size + "\r")
        sys.stdout.flush()


def select_pilatus_detecor(shape):
    """CrysalisPro only accepts some detector shapes as CBF inputs.
    Those shaped correspond to the one of the dectris detector Pilatus
    
    This function takes the input shape and return the smallest Dectris shape which is large enough. 
    """
    assert len(shape) >= 2
    valid_detectors = {  # (514, 1030): 'eiger_500k',
                         # (1065, 1030): 'eiger_1m',
                         # (2167, 2070): 'eiger_4m',
                         # (3269, 3110): 'eiger_9m',
                         # (4371, 4150): 'eiger_16m',
                         # (512, 1028): 'eiger2cdte500k',
                         # (1062, 1028): 'eiger2cdte1m',
                         # (2162, 2068): 'eiger2cdte4m',
                         # (3262, 3108): 'eiger2cdte9m',
                         # (4362, 4148): 'eiger2cdte16m',
                         # (1, 1280): 'mythen1280',
                         (195, 487): 'pilatus_100k',
                         (407, 487): 'pilatus_200k',
                         (619, 487): 'pilatus_300k',
                         (195, 1475): 'pilatus_300kw',
                         (1043, 981): 'pilatus_1m',
                         (1679, 1475): 'pilatus_2m',
                         (2527, 2463): 'pilatus_6m',
                         # (195, 4439): 'pilatus_900kw'
                         }
    best = None
    for k in valid_detectors:
        if k[0] >= shape[-2] and k[1] >= shape[-1]:
            if best is None:
                best = k
            elif k[0] < best[0] or k[1] < best[1]:
                best = k
    return best


def convert_one(input_filename, options, start_at=0):
    """
    Convert a single file using options

    :param str input_filename: The input filename
    :param object options: List of options provided from the command line
    :param start_at: index to start at for given file
    :rtype: int
    :returns: the number of frames processed
    """
    flip = bool((options.rotation // 90) % 2)
    if options.transpose:
        flip = not flip

    input_filename = os.path.abspath(input_filename)
    input_exists = os.path.exists(input_filename)

    if options.verbose:
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

    shape = source.shape[-1::-1] if flip else source.shape
    if options.pilatus:
        shape = select_pilatus_detecor(shape)

    pilatus_headers = cbfimage.PilatusHeader("Silicon sensor, thickness 0.001 m")
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
                            detector = "%s, S/N %s" % (nxdetector["detector_information/model"][()],
                                                 nxdetector["detector_information/name"][()])
                            pilatus_headers["Detector"] = detector
                        except Exception as e:
                            logger.warning("Error in searching for detector definition (%s): %s", type(e), e)
                        try:
                            pilatus_headers["Pixel_size"] = (nxdetector["detector_information/pixel_size/xsize"][()],
                                                             nxdetector["detector_information/pixel_size/ysize"][()])
                        except Exception as e:
                            logger.warning("Error in searching for pixel size (%s): %s", type(e), e)
                        try:
                            t1 = nxdetector["acquisition/exposure_time"][()]
                            t2 = nxdetector["acquisition/latency_time"][()]
                            pilatus_headers["Exposure_time"] = t1
                            pilatus_headers["Exposure_period"] = t1 + t2
                        except Exception as e:
                            logger.warning("Error in searching for exposure time (%s): %s", type(e), e)
    elif isinstance(source, eigerimage.EigerImage):
        raise NotImplementedError("Please implement Eiger detector data format parsing or at least open an issue")
    else:
        raise NotImplementedError("Unsupported format: %s" % source.__class__.__name__)

    # Parse option for Pilatus headers
    if options.energy:
        pilatus_headers["Wavelength"] = CONST_hc / options.energy
    elif options.wavelength:
        pilatus_headers["Wavelength"] = options.wavelength
    if options.distance:
        pilatus_headers["Detector_distance"] = options.distance
    if options.beam:
        pilatus_headers["Beam_xy"] = options.beam
    if options.alpha:
        pilatus_headers["Alpha"] = options.alpha
    if options.kappa:
        pilatus_headers["Kappa"] = options.kappa
    formula = None
    destination = None
    if options.chi is not None:
        try:
            value = float(options.chi)
        except ValueError:
            # Handle the string
            formula = numexpr.NumExpr(options.chi)
            destination = "Chi"
            pilatus_headers["Oscillation_axis"] = "CHI"
        else:
            pilatus_headers["Chi"] = value
            pilatus_headers["Chi_increment"] = 0.0

    if options.phi is not None:
        try:
            value = float(options.phi)
        except ValueError:
            # Handle the string
            formula = numexpr.NumExpr(options.phi)
            destination = "Phi"
            pilatus_headers["Oscillation_axis"] = "PHI"
        else:
            pilatus_headers["Phi"] = value
            pilatus_headers["Phi_increment"] = 0.0
    if options.omega is not None:
        try:
            value = float(options.omega)
        except ValueError:
            # Handle the string
            formula = numexpr.NumExpr(options.omega)
            destination = "Omega"
            pilatus_headers["Oscillation_axis"] = "OMEGA"
        else:
            pilatus_headers["Omega"] = value
            pilatus_headers["Omega_increment"] = 0.0

    if options.mask:
        mask = fabio_open(options.mask).data
        wmsk = numpy.where(mask)

    for i, frame in enumerate(source):
        idx = i + start_at
        data = numpy.empty(shape, dtype=numpy.int32)
        data.fill(options.dummy)
        input_data = frame.data.astype(numpy.int32)

        if options.mask:
            input_data[wmsk] = options.dummy

        if options.rotation:
            input_data = numpy.rot90(input_data, k=options.rotation // 90)
        if options.transpose:
            input_data = input_data.T
        if options.flip_ud:
            input_data = numpy.flipud(input_data)
        if options.flip_lr:
            input_data = numpy.fliplr(input_data)

        data[:input_data.shape[0],:input_data.shape[1]] = input_data

        mask = numpy.where(input_data == numpy.iinfo(frame.data.dtype).max)
        data[mask] = options.dummy
        converted = cbfimage.CbfImage(data=data)

        if formula and destination:
            position = formula(idx)
            delta = (formula(idx + 1) - position)
            pilatus_headers["Start_angle"] = pilatus_headers[destination] = position
            pilatus_headers["Angle_increment"] = pilatus_headers[destination + "_increment"] = delta
        converted.pilatus_headers = pilatus_headers

        output_filename = options.output.format(index=((idx + options.offset)))
        os.makedirs(os.path.dirname(output_filename), exist_ok=True)
        try:
            logger.debug("Write '%s'", output_filename)
            if not options.dry_run:
                converted.write(output_filename)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            logger.error("Saving output file '%s' failed cause: \"%s: %s\". Conversion skipped.", output_filename, type(e), e)
            logger.debug("Backtrace", exc_info=True)
            return -1
    return source.nframes


def convert_all(options):
    """Convert all the files from the command line.

    :param object options: List of options provided from the command line
    :rtype: bool
    :returns: True is the conversion succeeded
    """
    pb = ProgressBar("HDF5 --> CBFs", len(options.images), 30)
    succeeded = True
    start_at = 0
    for i, filename in enumerate(options.images):
        pb.update(i + 0.5, os.path.basename(filename))
        finish_at = convert_one(filename, options, start_at)
        succeeded = succeeded and (finish_at > 0)
        start_at += finish_at
    pb.clear()
    return succeeded


def main():

    epilog = """return codes: 0 means a success. 1 means the conversion
                contains a failure, 2 means there was an error in the
                arguments"""

    parser = argparse.ArgumentParser(prog="eiger2cbf",
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
#     group.add_argument("-l", "--list", action="store_true", dest="list", default=None,
#                        help="show the list of available formats and exit")
    group.add_argument("-o", "--output", default='eiger2cbf/frame_{index:04d}.cbf', type=str,
                       help="output directory and filename template: eiger2cbf/frame_{index:04d}.cbf")
    group.add_argument("-m", "--mask", type=str, default=None,
                       help="Read masked pixel from this file")
    group.add_argument("-O", "--offset", type=int, default=0,
                       help="index offset, CrysalisPro likes indexes to start at 1, Python starts at 0")
    group.add_argument("-D", "--dummy", type=int, default=-1,
                       help="Set masked values to this dummy value")
    group.add_argument("--pilatus", action="store_true", default=False,
                       help="Select an image shape similar to Pilatus detectors for compatibiliy with Crysalis")

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

    group = parser.add_argument_group("Experimental setup options")
    group.add_argument("-e", "--energy", type=float, default=None,
                       help="Energy of the incident beam in keV")
    group.add_argument("-w", "--wavelength", type=float, default=None,
                       help="Wavelength of the incident beam in Å")
    group.add_argument("-d", "--distance", type=float, default=None,
                       help="Detector distance in meters")
    group.add_argument("-b", "--beam", nargs=2, type=float, default=None,
                       help="Direct beam in pixels x, y")

    group = parser.add_argument_group("Goniometer setup")
#     group.add_argument("--axis", type=str, default=None,
#                        help="Goniometer angle used for scanning: 'omega', 'phi' or 'chi'")
    group.add_argument("--alpha", type=float, default=None,
                       help="Goniometer angle alpha value in deg.")
    group.add_argument("--kappa", type=float, default=None,
                       help="Goniometer angle kappa value in deg.")
    group.add_argument("--chi", type=str, default=None,
                       help="Goniometer angle chi value in deg. or formula f(index)")
    group.add_argument("--phi", type=str, default=None,
                       help="Goniometer angle phi value in deg. or formula f(index)")
    group.add_argument("--omega", type=str, default=None,
                       help="Goniometer angle omega value in deg. or formula f(index) like '-180+index*0.1")

    group = parser.add_argument_group("Image preprocessing (Important: applied in this order!)")
    group.add_argument("--rotation", type=int, default=0,
                       help="Rotate the initial image by this value in degrees. Must be a multiple of 90°.")
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

        if len(args.IMAGE) == 0:
            raise argparse.ArgumentError(None, "No input file specified.")

        # the upper case IMAGE is used for the --help auto-documentation
        args.images = expand_args(args.IMAGE)
        args.images.sort()
    except argparse.ArgumentError as e:
        logger.error(e.message)
        logger.debug("Backtrace", exc_info=True)
        return EXIT_ARGUMENT_FAILURE

    succeeded = convert_all(args)
    if not succeeded:
        print("Conversion or part of it failed. You can try with --debug to have more output information.")
        return EXIT_FAILURE

    return EXIT_SUCCESS


if __name__ == "__main__":
    result = main()
    sys.exit(result)
