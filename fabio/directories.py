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

"""FabIO module: Contains the directory with test-images"""
__author__ = "Jérôme Kieffer"
__contact__ = "Jerome.Kieffer@ESRF.eu"
__license__ = "GPLv3+"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__date__ = "29/10/2015"
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
