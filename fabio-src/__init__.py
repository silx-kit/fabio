#!/usr/bin/env python
# coding: utf-8
"""
FabIO module

"""
__author__ = "Jérôme Kieffer"
__contact__ = "Jerome.Kieffer@ESRF.eu"
__license__ = "GPLv3+"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__date__ = "21/07/2015"
__status__ = "stable"


import logging
logging.basicConfig()
from ._version import version, version_info, hexversion
from . import fabioimage
from . import openimage
from .fabioutils import COMPRESSORS, jump_filename, FilenameObject, \
        previous_filename, next_filename, deconstruct_filename, \
        extract_filenumber, getnum, construct_filename

# Compatibility with outside world:
filename_object = FilenameObject

from .openimage import openimage as open
from .openimage import openheader as openheader



def tests():
    """
    Run the FabIO test suite. 
    
    If the test-images are not already installed (via the debian package for example),
    they need to be downloaded from sourceforge.net, which make take a while.
    Ensure your network connection is operational and your proxy settings are correct,
    for example:
    
    export http_proxy=http://proxy.site.com:3128 
    """
    from . import test
    test.run_tests()
