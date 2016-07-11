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

"""
Converter module. 
This is for the moment empty (populated only with almost pass through anonymous functions)
but aims to be populated with more sofisticated translators ...  

"""
# get ready for python3
from __future__ import with_statement, print_function

__author__ = "Jérôme Kieffer"
__contact__ = "jerome.kieffer@esrf.eu"
__license__ = "GPLv3+"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"

import types, logging
logger = logging.getLogger("converter")

def convert_data_integer(data):
    """
    convert data to integer
    """
    if data is not None:
        return data.astype(int)
    else:
        return data


CONVERSION_HEADER = {
                     ("edfimage", "edfimage"): lambda header:header,
                     }
CONVERSION_DATA = {
                   ("edfimage", "edfimage"): lambda data:data,
                   ("edfimage", "cbfimage"): convert_data_integer,
                   ("edfimage", "mar345image"): convert_data_integer,
                   ("edfimage", "fit2dmaskimage"): convert_data_integer,
                   ("edfimage", "kcdimage"): convert_data_integer,
                   ("edfimage", "OXDimage"): convert_data_integer,
                   ("edfimage", "pnmimage"): convert_data_integer,
                   }

def convert_data(inp, outp, data):
    """
    Return data converted to the output format ... over-simplistic implementation for the moment ...
    @param inp,outp: input/output format like "cbfimage"
    @param data(ndarray): the actual dataset to be transformed
    """
    return CONVERSION_DATA.get((inp, outp), lambda data:data)(data)

def convert_header(inp, outp, header):
    """
    return header converted to the output format
    @param inp,outp: input/output format like "cbfimage"
    @param header(dict):the actual set of headers to be transformed 
    """
    return CONVERSION_HEADER.get((inp, outp), lambda header:header)(header)
