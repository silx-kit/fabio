#!/usr/bin/env python
#coding: utf-8
"""
FabIO module

"""
__author__ = "Jérôme Kieffer"
__contact__ = "Jerome.Kieffer@ESRF.eu"
__license__ = "GPLv3+"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__date__ = "14/01/2014"
__status__ = "stable"

version = "0.1.4"
import logging
logging.basicConfig()
from . import fabioimage
from . import openimage
from .fabioutils import COMPRESSORS, jump_filename, FilenameObject, \
        previous_filename, next_filename, deconstruct_filename, \
        extract_filenumber, getnum, construct_filename

# Compatibility with outside world:
filename_object = FilenameObject

from .openimage import openimage as open
from .openimage import openheader as openheader
