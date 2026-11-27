#
#    Project: X-ray image reader
#             https://github.com/silx-kit/fabio
#
#
#    Copyright (C) European Synchrotron Radiation Facility, Grenoble, France
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
# THE SOFTWARE

"""Read Pilatus and SAXSLAB metadata from Ganesha TIFF images."""

import logging
from typing import ClassVar
from xml.etree import ElementTree

from .pilatusimage import PilatusImage, PilatusTiffFrame

_logger = logging.getLogger(__name__)


class GaneshaTiffFrame(PilatusTiffFrame):
    """A TIFF frame with both detector and SAXSLAB parameters."""

    def __init__(self, data, tiff_header, pilatus_header, ganesha_header):
        super().__init__(data, tiff_header, pilatus_header)
        self.ganesha_header = ganesha_header
        self._header = pilatus_header.copy()
        self._header.update(ganesha_header)


class GaneshaImage(PilatusImage):
    """Read SAXSLAB Ganesha TIFF files using an explicit codec selection.

    Use ``fabio.factory("ganeshaimage").read(filename)``. Automatic TIFF
    subtype detection is not supported. ``header`` combines the Pilatus
    ImageDescription with the SAXSLAB parameters in Artist (tag 315).
    Values remain strings, or None for empty parameters. The first value
    is retained for duplicate SAXSLAB names; conflicting duplicates log
    a warning.
    """

    DESCRIPTION = "SAXSLAB Ganesha file format based on Tiff"
    # Until subtype detection exists, use this reader through explicit selection.
    DEFAULT_EXTENSIONS: ClassVar[list] = []

    def _create_ganesha_header(self, tiff_header):
        if "artist" not in tiff_header:
            raise OSError("Missing SAXSLAB parameters in TIFF Artist tag")
        root = ElementTree.fromstring(tiff_header["artist"])
        if root.tag != "SAXSLABparameters":
            raise OSError("TIFF Artist tag does not contain SAXSLAB parameters")
        header = self.check_header()
        for parameter in root.findall("param"):
            name = parameter.get("name")
            if name is None:
                continue
            value = "".join(parameter.itertext()) or None
            if name not in header:
                header[name] = value
            elif header[name] != value:
                _logger.warning(
                    "Conflicting SAXSLAB parameter %s: keeping %r instead of %r",
                    name,
                    header[name],
                    value,
                )
        return header

    def _create_frame(self, image_data, tiff_header):
        return GaneshaTiffFrame(
            image_data,
            tiff_header,
            self._create_pilatus_header(tiff_header),
            self._create_ganesha_header(tiff_header),
        )

    def read(self, fname, frame=None):
        super().read(fname, frame=frame)
        if self.lib is None:
            raise OSError("Unable to read Ganesha TIFF image")
        return self


ganeshaimage = GaneshaImage
