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

"""Helper functions using Python Imaging Library (PIL)
"""

__authors__ = ["Jérôme Kieffer", "Jon Wright"]
__date__ = "25/06/2018"
__license__ = "MIT"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__status__ = "stable"

import logging
import numpy

logger = logging.getLogger(__name__)

try:
    from PIL import Image
except ImportError:
    Image = None


PIL_TO_NUMPY = {
    "I;8": numpy.uint8,
    "I;16": numpy.uint16,
    "I;16B": numpy.uint16,  # big endian
    "I;16L": numpy.uint16,  # little endian
    "I;32": numpy.uint32,
    "I;32L": numpy.uint32,  # little endian
    "I;32B": numpy.uint32,  # big endian
    "F;32F": numpy.float32,
    "F;32BF": numpy.float32,  # big endian
    "F;64F": numpy.float64,
    "F;64BF": numpy.float64,  # big endian
    "F": numpy.float32,
    "1": bool,
    "I": numpy.int32,
    "L": numpy.uint8,
    "P": numpy.uint8,
}


NUMPY_TO_PIL = {
    'float32': "F",
    'int32': "F;32NS",
    'uint32': "F;32N",
    'int16': "F;16NS",
    'uint16': "F;16N",
    'int8': "F;8S",
    'uint8': "F;8"
}


def get_numpy_array(pil_image):
    """
    Returns a numpy array from a PIL image

    :param PIL.Image pil_image: A PIL Image object
    """
    dim1, dim2 = pil_image.size
    if pil_image.mode in PIL_TO_NUMPY:
        dtype = PIL_TO_NUMPY[pil_image.mode]
    else:
        dtype = numpy.float32
        pil_image = pil_image.convert("F")
    try:
        if pil_image.mode == 'P':
            # Indexed color
            data = numpy.asarray(pil_image.convert("RGB"), dtype)
        else:
            data = numpy.asarray(pil_image, dtype)
    except Exception:
        # This PIL version do not support buffer interface
        logger.debug("Backtrace", exc_info=True)
        if hasattr(pil_image, "tobytes"):
            data = numpy.frombuffer(pil_image.tobytes(), dtype=dtype).copy()
        else:
            data = numpy.frombuffer(pil_image.tobytes(), dtype=dtype).copy()
        # byteswap ?
        if numpy.dtype(dtype).itemsize > 1:
            need_swap = False
            need_swap |= numpy.little_endian and "B" in pil_image.mode
            need_swap |= not numpy.little_endian and pil_image.mode.endswith("L")
            if need_swap:
                data.byteswap(True)
        data = data.reshape((dim2, dim1))

    return data


def create_pil_16(numpy_array):
    """
    Convert a numpy array to a Python Imaging Library 16 bit greyscale image.

    :param numpy.ndarray numpy_array: A numpy array
    """
    if Image is None:
        raise ImportError("PIL is not installed")

    size = numpy_array.shape[:2][::-1]
    if numpy_array.dtype.name in NUMPY_TO_PIL:
        mode2 = NUMPY_TO_PIL[numpy_array.dtype.name]
        mode1 = mode2[0]
    else:
        raise RuntimeError("Unknown numpy type: %s" % (numpy_array.dtype.type))
    dats = numpy_array.tobytes()
    pil_image = Image.frombuffer(mode1, size, dats, "raw", mode2, 0, 1)

    return pil_image
