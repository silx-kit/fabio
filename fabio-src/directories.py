#!/usr/bin/env python
# coding: utf-8
"""
FabIO module

Contains the directory with test-images
"""
__author__ = "Jérôme Kieffer"
__contact__ = "Jerome.Kieffer@ESRF.eu"
__license__ = "GPLv3+"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__date__ = "23/01/2015"
__status__ = "stable"

import os, getpass, tempfile
import logging
logger = logging.getLogger("fabio.directories")

SHARED_TESTIMAGES = "/usr/share/fabio/testimages"

# testimages contains the directory name where test images are located
testimages = None
if "FABIO_TESTIMAGES" in os.environ:
    testimages = os.environ.get("FABIO_TESTIMAGES")
    if not os.path.exists(testimages):
        logger.warning("testimage directory %s does not exist" % testimages)
elif os.path.isdir(SHARED_TESTIMAGES):
    testimages = SHARED_TESTIMAGES
else:
    # create a temporary folder
    testimages = os.path.join(tempfile.gettempdir(), "fabio_testimages_%s" % (getpass.getuser()))

if not os.path.exists(testimages):
    os.makedirs(testimages)
