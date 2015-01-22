
from collections import namedtuple
_version_info = namedtuple("version_info", ["major", "minor", "micro", "releaselevel", "serial"])
MAJOR = 0
MINOR = 2
MICRO = 1
RELEV = "dev"  # <16
SERIAL = 0  # <16

version_info = _version_info(MAJOR, MINOR, MICRO, RELEV, SERIAL)

version = "%d.%d.%d" % version_info[:3]
if version_info.releaselevel != "final":
    version += "-%s%s" % version_info[-2:]

# This is called hexversion since it only really looks meaningful when viewed as the result of passing it to the built-in hex() function. The version_info value may be used for a more human-friendly encoding of the same information.
#
# The hexversion is a 32-bit number with the following layout:
# Bits (big endian order)     Meaning
# 1-8     PY_MAJOR_VERSION (the 2 in 2.1.0a3)
# 9-16     PY_MINOR_VERSION (the 1 in 2.1.0a3)
# 17-24     PY_MICRO_VERSION (the 0 in 2.1.0a3)
# 25-28     PY_RELEASE_LEVEL (0xA for alpha, 0xB for beta, 0xC for release candidate and 0xF for final)
# 29-32     PY_RELEASE_SERIAL (the 3 in 2.1.0a3, zero for final releases)
#
# Thus 2.1.0a3 is hexversion 0x020100a3.
RELEASE_LEVEL_VALUE = { "dev": 0, "alpha": 10, "beta": 11, "gamma": 11, "final":15}
hexversion = version_info[4]
hexversion |= RELEASE_LEVEL_VALUE.get(version_info[3], 0) * 1 << 4
hexversion |= version_info[2] * 1 << 8
hexversion |= version_info[1] * 1 << 16
hexversion |= version_info[0] * 1 << 24
