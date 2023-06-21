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

"""Converter module.

This is for the moment empty (populated only with almost pass through anonymous functions)
but aims to be populated with more sofisticated translators...

"""

__author__ = "Jérôme Kieffer"
__contact__ = "jerome.kieffer@esrf.eu"
__license__ = "MIT"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"

import logging
logger = logging.getLogger(__name__)


def convert_data_integer(data):
    """
    convert data to integer
    """
    if data is not None:
        return data.astype(int)
    else:
        return data


CONVERSION_HEADER = {
    ("edfimage", "edfimage"): lambda header: header,
}

CONVERSION_DATA = {
    ("edfimage", "edfimage"): lambda data: data,
    ("edfimage", "cbfimage"): convert_data_integer,
    ("edfimage", "mar345image"): convert_data_integer,
    ("edfimage", "fit2dmaskimage"): convert_data_integer,
    ("edfimage", "kcdimage"): convert_data_integer,
    ("edfimage", "OXDimage"): convert_data_integer,
    ("edfimage", "pnmimage"): convert_data_integer,
}


def convert_data(inp, outp, data):
    """
    Return data converted to the output format ... over-simplistic
    implementation for the moment...

    :param str inp: input format (like "cbfimage")
    :param str outp: output format (like "cbfimage")
    :param numpy.ndarray data: the actual dataset to be transformed
    """
    return CONVERSION_DATA.get((inp, outp), lambda data: data)(data)


def convert_header(inp, outp, header):
    """
    Return header converted to the output format

    :param str inp: input format (like "cbfimage")
    :param str outp: output format (like "cbfimage")
    :param dict header: the actual set of headers to be transformed
    """
    return CONVERSION_HEADER.get((inp, outp), lambda header: header)(header)
