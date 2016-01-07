# coding: utf-8
#
#    Project: X-ray image reader
#             https://github.com/kif/fabio
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

"""Simple module to handle versions"""

from __future__ import absolute_import, print_function, division

__author__ = "Jerome Kieffer"
__contact__ = "Jerome.Kieffer@ESRF.eu"
__license__ = "GPLv3+"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__date__ = "17/12/2015"
__status__ = "beta"
__docformat__ = 'restructuredtext'
__doc__ = """

Module for version handling:

provides:
* version = "1.2.3" or "1.2.3-beta4"
* version_info = named tuple (1,2,3,"beta",4)
* hexversion: 0x010203B4

This is called hexversion since it only really looks meaningful when viewed as the
result of passing it to the built-in hex() function.
The version_info value may be used for a more human-friendly encoding of the same information.

The hexversion is a 32-bit number with the following layout:
Bits (big endian order)     Meaning
1-8     PY_MAJOR_VERSION (the 2 in 2.1.0a3)
9-16     PY_MINOR_VERSION (the 1 in 2.1.0a3)
17-24     PY_MICRO_VERSION (the 0 in 2.1.0a3)
25-28     PY_RELEASE_LEVEL (0xA for alpha, 0xB for beta, 0xC for release candidate and 0xF for final)
29-32     PY_RELEASE_SERIAL (the 3 in 2.1.0a3, zero for final releases)

Thus 2.1.0a3 is hexversion 0x020100a3.

"""

RELEASE_LEVEL_VALUE = { "dev": 0,
                       "alpha": 10,
                       "beta": 11,
                       "gamma": 11,
                       "rc": 12,
                       "final":15}

MAJOR = 0
MINOR = 3
MICRO = 0
RELEV = "final"  # <16
SERIAL = 0  # <16


from collections import namedtuple
_version_info = namedtuple("version_info", ["major", "minor", "micro", "releaselevel", "serial"])

version_info = _version_info(MAJOR, MINOR, MICRO, RELEV, SERIAL)

strictversion = version = "%d.%d.%d" % version_info[:3]
if version_info.releaselevel != "final":
    version += "-%s%s" % version_info[-2:]
    prerel = "a" if RELEASE_LEVEL_VALUE.get(version_info[3], 0) < 10 else "b"
    if prerel not in "ab":
        prerel = "a"
    strictversion += prerel + str(version_info[-1])

hexversion = version_info[4]
hexversion |= RELEASE_LEVEL_VALUE.get(version_info[3], 0) * 1 << 4
hexversion |= version_info[2] * 1 << 8
hexversion |= version_info[1] * 1 << 16
hexversion |= version_info[0] * 1 << 24

