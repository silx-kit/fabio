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
__date__ = "14/09/2020"
__status__ = "production"

import logging
logging.basicConfig()

import sys
import os
import glob

import fabio
import argparse

logger = logging.getLogger("eiger2cbf")



def expand_args(args):
    """
    Takes an argv and expand it (under Windows, cmd does not convert *.tif into
    a list of files.

    :param list args: list of files or wildcards
    :return: list of actual args
    """
    new = []
    for afile in args:
        if glob.has_magic(afile):
            new += glob.glob(afile)
        else:
            new.append(afile)
    return new


EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EXIT_ARGUMENT_FAILURE = 2


def main():

    epilog = """return codes: 0 means a success. 1 means the conversion
                contains a failure, 2 means there was an error in the
                arguments"""

    parser = argparse.ArgumentParser(prog="eiger2cbf",
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
    group.add_argument("-F", "--output-format", dest="format", type=str, default="cbf",
                       help="output format")

    group = parser.add_argument_group("optional behaviour arguments")
    group.add_argument("-f", "--force", dest="force", action="store_true", default=False,
                       help="if an existing destination file cannot be" +
                       " opened, remove it and try again (this option" +
                       " is ignored when the -n option is also used)")
    group.add_argument("-n", "--no-clobber", dest="no_clobber", action="store_true", default=False,
                       help="do not overwrite an existing file (this option" +
                       " is ignored when the -i option is also used)")
    group.add_argument("--remove-destination", dest="remove_destination", action="store_true", default=False,
                       help="remove each existing destination file before" +
                       " attempting to open it (contrast with --force)")
    group.add_argument("-u", "--update", dest="update", action="store_true", default=False,
                       help="copy only when the SOURCE file is newer" +
                       " than the destination file or when the" +
                       " destination file is missing")
    group.add_argument("-i", "--interactive", dest="interactive", action="store_true", default=False,
                       help="prompt before overwrite (overrides a previous -n" +
                       " option)")
    group.add_argument("--dry-run", dest="dry_run", action="store_true", default=False,
                       help="do everything except modifying the file system")

    try:
        args = parser.parse_args()

        if args.debug:
            logger.setLevel(logging.DEBUG)

        if args.list:
            print_supported_formats()
            return

        if len(args.IMAGE) == 0:
            raise argparse.ArgumentError(None, "No input file specified.")

        # the upper case IMAGE is used for the --help auto-documentation
        args.images = expand_args(args.IMAGE)
        args.images.sort()

        if args.format is None or not args.format.endswith("image"):

            if args.format is None:
                if args.output is None:
                    raise argparse.ArgumentError(None, "No format specified. Use -F or -o.")
                dummy_filename = args.output
            else:
                # format looks to be an extension
                dummy_filename = "foo." + args.format

            # extract file format from file name
            filename = fabio.fabioutils.FilenameObject(filename=dummy_filename)

            if filename.format is None or len(filename.format) == 0:
                raise argparse.ArgumentError(None, "This file extension is unknown. You have also to specify a format using -F.")
            elif filename.format is None or len(filename.format) > 1:
                formats = [i + "image" for i in filename.format]
                formats = ', '.join(formats)
                raise argparse.ArgumentError(None, "This file extension correspond to different file formats: '%s'. You have to specify it using -F." % formats)
            args.format = filename.format[0] + "image"

        if not is_format_supported(args.format):
            raise argparse.ArgumentError(None, "Format '%s' is unknown. Use -l to list all available formats." % args.format)
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
