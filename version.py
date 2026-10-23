#!/usr/bin/env python3
#
#    Project: X-ray image reader
#             https://github.com/silx-kit/fabio
#
#    Copyright (C) 2015-2026 European Synchrotron Radiation Facility, Grenoble, France
#
#    Principal author:       Jérôme Kieffer (Jerome.Kieffer@ESRF.eu)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""Unique place where the version number is defined.

Module for version handling:

provides:
* version = "1.2.3" or "1.2.3-beta4"
* version_info = named tuple (1,2,3,"beta",4)
* hexversion: 0x010203B4
* strictversion = "1.2.3b4"
* debianversion = "1.2.3~beta4"
* calc_hexversion: the function to transform a version_tuple into an integer

This is called hexversion since it only really looks meaningful when viewed as the
result of passing it to the built-in hex() function.
The version_info value may be used for a more human-friendly encoding of the same information.

The hexversion is an integer with the following layout, taken from Python's `sys.hexversion`
(the 4 lowest fields use 24 bits: 8 bits each for minor and micro, 4 bits each for level and serial):
Bits (big endian order)     Meaning
1-8     PY_MAJOR_VERSION (the 2 in 2.1.0a3)
9-16     PY_MINOR_VERSION (the 1 in 2.1.0a3)
17-24     PY_MICRO_VERSION (the 0 in 2.1.0a3)
25-28     PY_RELEASE_LEVEL (0xA for alpha, 0xB for beta, 0xC for release candidate and 0xF for final)
29-32     PY_RELEASE_SERIAL (the 3 in 2.1.0a3, zero for final releases)

Thus 2.1.0a3 is hexversion 0x020100a3.

The major version is the highest field and is *not* limited to 8 bits: FabIO uses the
year as major version (2026.10.0), so `hexversion` is wider than 32 bits (0x7ea0a0000 for 2026.10.0a0).
It still increases with the version number, which is what it is used for.
The lower fields cannot overflow: minor and micro must be below 256, the serial below 16,
otherwise `calc_hexversion` raises a `ValueError`.

Version strings are accepted by `calc_hexversion(string=...)` in the forms "1.2.3" (final release),
"1.2.3a4", "1.2.3-a4", "1.2.3b4", "1.2.3rc1" or with the long names ("1.2.3-beta4").
A development version ("dev" release level, whose `version` string is written "-a0")
is parsed as an alpha, since the strings do not distinguish them.

"""
import re
from typing import NamedTuple

__author__ = "Jérôme Kieffer"
__contact__ = "Jerome.Kieffer@ESRF.eu"
__license__ = "MIT"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__date__ = "15/06/2026"
__status__ = "production"
__docformat__ = "restructuredtext"
__all__ = [
    "calc_hexversion",
    "date",
    "debianversion",
    "hexversion",
    "strictversion",
    "version_info",
]


RELEASE_LEVEL_VALUE = {"dev": 0, "alpha": 10, "beta": 11, "candidate": 12, "final": 15}

PRERELEASE_NORMALIZED_NAME = {"dev": "a", "alpha": "a", "beta": "b", "candidate": "rc"}

_PATTERN = re.compile(r"(\d+)\.(\d+)\.(\d+)(?:[-~.]?(dev|alpha|a|beta|b|candidate|rc|c)(\d*))?$")
"""Version string: major.minor.micro, then optionally a release level (with optional separator) and a serial"""

_LEVEL_ALIASES = {
    "dev": "dev",
    "a": "alpha",
    "alpha": "alpha",
    "b": "beta",
    "beta": "beta",
    "c": "candidate",
    "rc": "candidate",
    "candidate": "candidate",
}

MAJOR = 2026
MINOR = 10
MICRO = 0
RELEV = "dev"  # <16
SERIAL = 0       # <16
date = __date__

class _VersionInfo(NamedTuple):
    major: int
    minor: int
    micro: int
    releaselevel: str
    serial: int

class _DatedVersion(NamedTuple):
    version: str
    date: str

version_info = _VersionInfo(MAJOR, MINOR, MICRO, RELEV, SERIAL)


strictversion = version = debianversion = f"{version_info[0]}.{version_info[1]}.{version_info[2]}"
if version_info.releaselevel != "final":
    _prerelease = PRERELEASE_NORMALIZED_NAME[version_info[3]]
    version += f"-{_prerelease}{version_info[-1]}"
    debianversion += (
        f"~adev{version_info[-1]}"
        if RELEV == "dev"
        else f"~{_prerelease}{version_info[-1]}"
    )
    strictversion += _prerelease + str(version_info[-1])
dated_version = _DatedVersion(version=version, date=date)



def calc_hexversion(major=0, minor=0, micro=0, releaselevel="dev", serial=0, string=None):
    """Calculate the hexadecimal version number from the tuple version_info:

    :param major: integer (not limited, see the module documentation)
    :param minor: integer, from 0 to 255
    :param micro: integer, from 0 to 255
    :param releaselevel: integer (0 to 15) or string, one of the keys of `RELEASE_LEVEL_VALUE`
    :param serial: integer, from 0 to 15
    :param string: version number as a string like "1.2.3", "1.2.3a4", "1.2.3-beta4" or "1.2.3rc1".
        When provided, it overrides the other parameters; a string without suffix is a final release.
    :return: integer always increasing with revision numbers
    :raises ValueError: for an invalid string, an unknown release level or a field out of range
    """
    if string is not None:
        result = _PATTERN.match(string)
        if result is None:
            raise ValueError(f"'{string}' is not a valid version")
        major, minor, micro = (int(i) for i in result.group(1, 2, 3))
        if result.group(4) is None:
            releaselevel, serial = "final", 0
        else:
            releaselevel = _LEVEL_ALIASES[result.group(4)]
            serial = int(result.group(5) or 0)

    try:
        releaselevel = int(releaselevel)
    except ValueError:
        try:
            releaselevel = RELEASE_LEVEL_VALUE[releaselevel]
        except KeyError:
            raise ValueError(f"Unknown release level '{releaselevel}'") from None

    major, minor, micro, serial = int(major), int(minor), int(micro), int(serial)
    for name, value, limit in (("major", major, None), ("minor", minor, 256), ("micro", micro, 256),
                               ("releaselevel", releaselevel, 16), ("serial", serial, 16)):
        if value < 0 or (limit is not None and value >= limit):
            raise ValueError(f"The {name} number of the version is out of range: {value}")

    hex_version = serial
    hex_version |= releaselevel << 4
    hex_version |= micro << 8
    hex_version |= minor << 16
    hex_version |= major << 24
    return hex_version


hexversion = calc_hexversion(*version_info)
citation = "doi:10.1107/S0021889813000150"

if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser(usage="print the version of the software")
    parser.add_argument("--wheel", action="store_true", dest="wheel", default=None,
                        help="print version formated for wheel")
    parser.add_argument("--debian", action="store_true", dest="debian", default=None,
                        help="print version formated for debian")
    options = parser.parse_args()
    if options.debian:
        print(debianversion)
    elif options.wheel:
        print(strictversion)
    else:
        print(version)
