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
"""Portable image converter based on FabIO library.
"""

__author__ = "Valentin Valls"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__licence__ = "MIT"
__date__ = "23/04/2021"
__status__ = "production"

import logging
logging.basicConfig()

import sys
import os
import fabio
from fabio import fabioformats, fabioutils
from fabio.utils.cli import expand_args
import argparse

logger = logging.getLogger("fabio-convert")


def get_default_extension_from_format(format_name):
    """"
    Get a default file extension from a fabio format

    :param str format: String format like "edfimage"
    :rtype: str
    """
    class_ = fabioformats.get_class_by_name(format_name)
    if class_ is None:
        raise RuntimeError("Format '%s' unsupported" % format_name)

    extensions = class_.DEFAULT_EXTENSIONS
    if len(extensions) == 0:
        # No extensions
        return ""
    else:
        return extensions[0]


def get_output_filename(input_filename, format_name):
    """
    Returns the output filename from the input filename and the format.

    :param str input_filename: Input filename path
    :param str format_name: String format like "edfimage"
    :rtype: str
    """
    basename, _ = os.path.splitext(input_filename)
    extension = get_default_extension_from_format(format_name)
    if extension == "":
        extension = "bin"
    return basename + "." + extension


def is_user_want_to_overwrite_filename(filename):
    """
    Ask question in the shell and returns true if the user want to overwrite
    a file passed in parameter.

    :param str filename: The filename it asks for
    :rtype: bool
    """
    while True:
        question = "Do you want to overwrite the file '%s' (y/n): " % filename
        answer = input(question).strip().lower()
        if answer in ["y", "yes", "n", "no"]:
            break
    return answer in ["y", "yes"]


def is_older(filename1, filename2):
    """Returns true if the first file is older than the second one.

    :param str filename1: An existing filename
    :param str filename2: An existing filename
    :rtype: bool
    """
    time1 = os.path.getmtime(filename1)
    time2 = os.path.getmtime(filename2)
    return time1 > time2


def convert_one(input_filename, output_filename, options):
    """
    Convert a single file using options

    :param str input_filename: The input filename
    :param str output_filename: The output filename
    :param object options: List of options provided from the command line
    :rtype: bool
    :returns: True is the conversion succeeded
    """
    input_filename = os.path.abspath(input_filename)
    input_exists = os.path.exists(input_filename)
    output_filename = os.path.abspath(output_filename)
    output_exists = os.path.exists(output_filename)

    if options.verbose:
        print("Converting file '%s' to '%s'" % (input_filename, output_filename))

    if not input_exists:
        logger.error("Input file '%s' do not exists. Conversion skipped.", input_filename)
        return False

    skip_conversion = False
    remove_file = False

    if output_exists:
        if options.interactive:
            if is_user_want_to_overwrite_filename(output_filename):
                remove_file = True
            else:
                skip_conversion = True
        elif options.no_clobber:
            skip_conversion = True
        elif options.force or options.remove_destination:
            remove_file = True
        elif options.update:
            if is_older(output_filename, input_filename):
                skip_conversion = True
            else:
                remove_file = True
        elif is_user_want_to_overwrite_filename(output_filename):
                remove_file = True
        else:
            skip_conversion = True

    if remove_file:
        if options.verbose:
            print("Overwrite file %s" % output_filename)
        try:
            if not options.dry_run:
                os.remove(output_filename)
        except OSError as e:
            logger.error("Removing previous file %s failed cause: \"%s\". Conversion skipped.", e.message, output_filename)
            logger.debug("Backtrace", exc_info=True)
            return False

    if skip_conversion:
        if options.verbose:
            print("Conversion to file %s skipped" % output_filename)
        return True

    try:
        logger.debug("Load '%s'", input_filename)
        source = fabio.open(input_filename)
    except KeyboardInterrupt:
        raise
    except Exception as e:
        logger.error("Loading input file '%s' failed cause: \"%s\". Conversion skipped.", input_filename, e.message)
        logger.debug("Backtrace", exc_info=True)
        return False

    try:
        logger.debug("Convert '%s' into '%s'", input_filename, options.format)
        converted = source.convert(options.format)
    except KeyboardInterrupt:
        raise
    except Exception as e:
        logger.error("Converting input file '%s' failed cause: \"%s\". Conversion skipped.", input_filename, e.message)
        logger.debug("Backtrace", exc_info=True)
        return False

    try:
        logger.debug("Write '%s'", output_filename)
        if not options.dry_run:
            converted.write(output_filename)
    except KeyboardInterrupt:
        raise
    except Exception as e:
        logger.error("Saving output file '%s' failed cause: \"%s\". Conversion skipped.", output_filename, e.message)
        logger.debug("Backtrace", exc_info=True)
        return False

    # a success
    return True


def convert_all(options):
    """Convert all the files from the command line.

    :param object options: List of options provided from the command line
    :rtype: bool
    :returns: True is the conversion succeeded
    """
    succeeded = True
    for filename in options.images:

        if options.output is None:
            output_filename = get_output_filename(filename, options.format)
        elif os.path.isdir(options.output):
            output_filename = get_output_filename(filename, options.format)
            output_filename = os.path.basename(output_filename)
            directory = os.path.abspath(options.output)
            output_filename = os.path.join(directory, output_filename)
        else:
            output_filename = options.output

        succeeded = succeeded and convert_one(filename, output_filename, options)

    return succeeded


def print_supported_formats():
    """List supported format to the output"""
    classes = fabioformats.get_classes(writer=True)
    classes.sort(key=lambda c: c.__module__.lower())

    indentation = "    "

    print(f"List of writable file formats supported by FabIO version {fabio.version}")
    print()

    for class_ in classes:
        if len(class_.DEFAULT_EXTENSIONS) > 0:
            extensions = ", ".join(["*." + x for x in class_.DEFAULT_EXTENSIONS])
            extensions = "(%s)" % extensions
        else:
            extensions = ""

        print("- %s %s" % (class_.codec_name(), extensions))
        print("%s%s" % (indentation, class_.DESCRIPTION))


def is_format_supported(format_name):
    """
    Returns true if the file format is supported.

    :param str format_name: Name of the format (for example edfimage)
    :rtype: bool
    """
    try:
        fabio.factory(format_name)
        return True
    except RuntimeError:
        logger.debug("Backtrace", exc_info=True)
        return False


EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EXIT_ARGUMENT_FAILURE = 2


def main():

    epilog = """return codes: 0 means a success. 1 means the conversion
                contains a failure, 2 means there was an error in the
                arguments"""

    parser = argparse.ArgumentParser(prog="fabio-convert",
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
    group.add_argument("-F", "--output-format", dest="format", type=str, default=None,
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
            filename = fabioutils.FilenameObject(filename=dummy_filename)

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
