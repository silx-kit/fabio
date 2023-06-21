# coding: utf-8
#
#    Project: X-ray image reader
#             https://github.com/silx-kit/fabio
#
#    Principal author:       "Brian R. Pauw" "brian@stack.nl"
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

"""

Authors: Brian R. Pauw
email:  brian@stack.nl

Written using information gleaned from the ReadRAXISImage program
written by T. L. Hendrixson, made available by Rigaku Americas.
Available at: http://www.rigaku.com/downloads/software/readimage.html


"""

__authors__ = ["Brian R. Pauw"]
__contact__ = "brian@stack.nl"
__license__ = "MIT"
__copyright__ = "Brian R. Pauw"
__date__ = "03/04/2020"

import logging
import struct
import os
import numpy
from .fabioimage import FabioImage
from .fabioutils import OrderedDict
logger = logging.getLogger(__name__)

RIGAKU_KEYS = OrderedDict([
    ('InstrumentType', 10),
    ('Version', 10),
    ('Crystal Name', 20),
    ('Crystal System', 12),
    ('A', 'float'),
    ('B', 'float'),
    ('C', 'float'),
    ('Alpha', 'float'),
    ('Beta', 'float'),
    ('Gamma', 'float'),
    ('Space Group', 12),
    ('Mosaicity', 'float'),
    ('Memo', 80),
    ('Date', 12),
    ('Reserved Space 1', 84),
    ('User', 20),
    ('Xray Target', 4),
    ('Wavelength', 'float'),
    ('Monochromator', 20),
    ('Monochromator 2theta', 'float'),
    ('Collimator', 20),
    ('Filter', 4),
    ('Crystal-to-detector Distance', 'float'),
    ('Generator Voltage', 'float'),
    ('Generator Current', 'float'),
    ('Focus', 12),
    ('Xray Memo', 80),
    ('IP shape', 'long'),  # 1= cylindrical, 0=flat. A "long" is overkill.
    ('Oscillation Type', 'float'),  # 1=weissenberg. else regular. "float"? really?
    ('Reserved Space 2', 56),
    ('Crystal Mount (spindle axis)', 4),
    ('Crystal Mount (beam axis)', 4),
    ('Phi Datum', 'float'),  # degrees
    ('Phi Oscillation Start', 'float'),  # deg
    ('Phi Oscillation Stop', 'float'),  # deg
    ('Frame Number', 'long'),
    ('Exposure Time', 'float'),  # minutes
    ('Direct beam X position', 'float'),  # special, x,y
    ('Direct beam Y position', 'float'),  # special, x,y
    ('Omega Angle', 'float'),  # omega angle
    ('Chi Angle', 'float'),  # omega angle
    ('2Theta Angle', 'float'),  # omega angle
    ('Mu Angle', 'float'),  # omega angle
    ('Image Template', 204),  # used for storing scan template..
    ('X Pixels', 'long'),
    ('Y Pixels', 'long'),
    ('X Pixel Length', 'float'),  # mm
    ('Y Pixel Length', 'float'),  # mm
    ('Record Length', 'long'),
    ('Total', 'long'),
    ('Starting Line', 'long'),
    ('IP Number', 'long'),
    ('Photomultiplier Ratio', 'float'),
    ('Fade Time (to start of read)', 'float'),
    ('Fade Time (to end of read)', 'float'),  # good that they thought of this, but is it applied?
    ('Host Type/Endian', 10),
    ('IP Type', 10),
    ('Horizontal Scan', 'long'),  # 0=left->Right, 1=Rigth->Left
    ('Vertical Scan', 'long'),  # 0=down->up, 1=up->down
    ('Front/Back Scan', 'long'),  # 0=front, 1=back
    ('Pixel Shift (RAXIS V)', 'float'),
    ('Even/Odd Intensity Ratio (RAXIS V)', 'float'),
    ('Magic number', 'long'),  # 'RAPID'-specific
    ('Number of Axes', 'long'),
    ('Goniometer Vector ax.1.1', 'float'),
    ('Goniometer Vector ax.1.2', 'float'),
    ('Goniometer Vector ax.1.3', 'float'),
    ('Goniometer Vector ax.2.1', 'float'),
    ('Goniometer Vector ax.2.2', 'float'),
    ('Goniometer Vector ax.2.3', 'float'),
    ('Goniometer Vector ax.3.1', 'float'),
    ('Goniometer Vector ax.3.2', 'float'),
    ('Goniometer Vector ax.3.3', 'float'),
    ('Goniometer Vector ax.4.1', 'float'),
    ('Goniometer Vector ax.4.2', 'float'),
    ('Goniometer Vector ax.4.3', 'float'),
    ('Goniometer Vector ax.5.1', 'float'),
    ('Goniometer Vector ax.5.2', 'float'),
    ('Goniometer Vector ax.5.3', 'float'),
    ('Goniometer Start ax.1', 'float'),
    ('Goniometer Start ax.2', 'float'),
    ('Goniometer Start ax.3', 'float'),
    ('Goniometer Start ax.4', 'float'),
    ('Goniometer Start ax.5', 'float'),
    ('Goniometer End ax.1', 'float'),
    ('Goniometer End ax.2', 'float'),
    ('Goniometer End ax.3', 'float'),
    ('Goniometer End ax.4', 'float'),
    ('Goniometer End ax.5', 'float'),
    ('Goniometer Offset ax.1', 'float'),
    ('Goniometer Offset ax.2', 'float'),
    ('Goniometer Offset ax.3', 'float'),
    ('Goniometer Offset ax.4', 'float'),
    ('Goniometer Offset ax.5', 'float'),
    ('Goniometer Scan Axis', 'long'),
    ('Axes Names', 40),
    ('file', 16),
    ('cmnt', 20),
    ('smpl', 20),
    ('iext', 'long'),
    ('reso', 'long'),
    ('save', 'long'),
    ('dint', 'long'),
    ('byte', 'long'),
    ('init', 'long'),
    ('ipus', 'long'),
    ('dexp', 'long'),
    ('expn', 'long'),
    ('posx', 20),
    ('posy', 20),
    ('xray', 'long'),
    # more values can be added here
    ('Header Leftovers', -1)
])


class RaxisImage(FabioImage):
    """
    FabIO image class to read Rigaku RAXIS image files.
    Write functions are not planned as there are plenty of more suitable
    file formats available for storing detector data.
    In particular, the MSB used in Rigaku files is used in an uncommon way:
    it is used as a *multiply-by* flag rather than a normal image value bit.
    While it is said to multiply by the value specified in the header, there
    is at least one case where this is found not to hold, so YMMV and be careful.
    """

    DESCRIPTION = "Rigaku RAXIS file format"

    DEFAULT_EXTENSIONS = ["img"]

    def __init__(self, *arg, **kwargs):
        """
        Generic constructor
        """
        FabioImage.__init__(self, *arg, **kwargs)
        self._dtype = numpy.dtype('uint16')  # same for all RAXIS images AFAICT
        self.endianness = '>'  # this may be tested for.

    def swap_needed(self):
        """not sure if this function is needed"""
        endian = self.endianness
        # Decide if we need to byteswap
        if (endian == '<' and numpy.little_endian) or (endian == '>' and not numpy.little_endian):
            return False
        if (endian == '>' and numpy.little_endian) or (endian == '<' and not numpy.little_endian):
            return True

    def _readheader(self, infile):
        """
        Read and decode the header of a Rigaku RAXIS image.
        The Rigaku format uses a block of (at least) 1400 bytes for storing
        information. The information has a fixed structure, but endianness
        can be flipped for non-char values. Header items which are not
        capitalised form part of a non-standardized data block and may not
        be accurate.

        TODO: It would be useful to have an automatic endianness test in here.

        :param infile: Opened python file (can be stringIO or bzipped file)
        """
        endianness = self.endianness
        # list of header key to keep the order (when writing)
        self.header = self.check_header()

        # swapBool=False
        fs = endianness
        minHeaderLength = 1400  # from rigaku's def
        # if (numpy.little_endian and endianness=='>'):
        #    swapBool=True
        # file should be open already
        # fh=open(filename,'rb')
        infile.seek(0)  # hopefully seeking works.
        rawHead = infile.read(minHeaderLength)
        # fh.close() #don't like open files in case of intermediate crash

        curByte = 0
        for key, kind in RIGAKU_KEYS.items():
            if isinstance(kind, int):
                # read a number of bytes, convert to char.
                # if -1, read remainder of header
                if kind == -1:
                    rByte = len(rawHead) - curByte
                    self.header[key] = struct.unpack(fs + str(rByte) + 's',
                                                     rawHead[curByte: curByte + rByte])[0]
                    curByte += rByte
                    break

                rByte = kind
                self.header[key] = struct.unpack(fs + str(rByte) + 's',
                                                 rawHead[curByte: curByte + rByte])[0]
                curByte += rByte
            elif kind == 'float':
                # read a float, 4 bytes
                rByte = 4
                self.header[key] = struct.unpack(fs + 'f',
                                                 rawHead[curByte: curByte + rByte])[0]
                curByte += rByte
            elif kind == 'long':
                # read a long, 4 bytes
                rByte = 4
                self.header[key] = struct.unpack(fs + 'l',
                                                 rawHead[curByte: curByte + rByte])[0]
                curByte += rByte
            else:
                logger.warning('special header data type %s not understood', kind)
            if len(rawHead) == curByte:
                # "end reached"
                break

    def read(self, fname, frame=None):
        """
        try to read image
        :param fname: name of the file
        :param frame:
        """
        self.resetvals()
        infile = self._open(fname, 'rb')
        offset = -1  # read from EOF backward
        self._readheader(infile)

        # we read the required bytes from the end of file, using code
        # lifted from binaryimage
        # read the image data

        dim1 = self.header['X Pixels']
        dim2 = self.header['Y Pixels']
        self._shape = dim2, dim1

        self._dtype = numpy.dtype(numpy.uint16)
        shape = self.shape
        size = shape[0] * shape[1] * self._dtype.itemsize
        if offset >= 0:
            infile.seek(offset)
        else:
            try:
                attrs = dir(infile)
                if "measure_size" in attrs:  # Handle specifically gzip
                    infile.seek(infile.measure_size() - size)  # seek from EOF backwards
                elif "size" in attrs:
                    infile.seek(infile.size - size)  # seek from EOF backwards
                if "len" in attrs:
                    infile.seek(infile.len - size)  # seek from EOF backwards
                else:
                    infile.seek(-size + offset + 1, os.SEEK_END)  # seek from EOF backwards
            except IOError as error:
                logger.warning('expected datablock too large, please check bytecode settings: %s, IOError: %s' % (self._dtype.type, error))
            except Exception as error:
                logger.error('Uncommon error encountered when reading file: %s' % error)
        rawData = infile.read(size)
        data = numpy.frombuffer(rawData, self._dtype).copy().reshape(shape)
        if self.swap_needed():
            data.byteswap(True)
        di = (data >> 15) != 0  # greater than 2^15
        if di.sum() >= 1:
            # find indices for which we need to do the correction (for which
            # the 16th bit is set):

            logger.debug("Correct for PM: %s" % di.sum())
            data = data << 1 >> 1  # reset bit #15 to zero
            self._dtype = numpy.dtype(numpy.uint32)
            data = data.astype(self._dtype)
            # Now we do some fixing for Rigaku's refusal to adhere to standards:
            sf = self.header['Photomultiplier Ratio']
            # multiply by the ratio  defined in the header
            # data[di] *= sf
            data[di] = (sf * data[di]).astype(self._dtype)

        self.data = data
        self._shape = None
        self._dtype = None
        return self

    def rigakuKeys(self):
        # returns dict of keys and keyLengths
        RKey = RIGAKU_KEYS
        orderList = list(RIGAKU_KEYS.keys())
        return RKey, orderList


raxisimage = RaxisImage
