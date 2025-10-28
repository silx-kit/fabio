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
#  FROM, OUT OF OR IN CONNECTION W

"""FabIO module: Contains the directory with test-images"""

__author__ = "Jérôme Kieffer"
__contact__ = "Jerome.Kieffer@ESRF.eu"
__license__ = "MIT"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__date__ = "24/07/2017"
__status__ = "stable"

import os
import getpass
import tempfile
import logging

logger = logging.getLogger(__name__)

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
    testimages = os.path.join(
        tempfile.gettempdir(), "fabio_testimages_%s" % (getpass.getuser())
    )

if not os.path.exists(testimages):
    os.makedirs(testimages)
