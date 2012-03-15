#!/usr/bin/env python 
#coding: utf8
"""
Converter module. 
This is for the moment empty (populated only with almost pass through anonymous functions)
but aims to be populated with more sofisticated translators ...  

"""
__author__ = "Jérôme Kieffer"
__contact__ = "jerome.kieffer@esrf.eu"
__license__ = "GPLv3+"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"

import os, types, logging, sys
logger = logging.getLogger("converter")
import numpy

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

def convert_data(input, output, data):
    """
    Return data converted to the output format ... over-simplistic implementation for the moment ...
    @param input,output: input/output format like "cbfimage"
    @param data(ndarray): the actual dataset to be transformed
    """
    return CONVERSION_DATA.get((input, output), lambda data:data)(header)

def convert_header(input, output, header):
    """
    return header converted to the output format
    @param input,output: input/output format like "cbfimage"
    @param header(dict):the actual set of headers to be transformed 
    """
    return CONVERSION_HEADER.get((input, output), lambda header:header)(header)
