# coding: utf-8
#
#    Project: CCD mask image reader/writer. Format used in CrysalisPro software 
#             https://github.com/silx-kit/fabio
#
#    Copyright (C) European Synchrotron Radiation Facility, Grenoble, France
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
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#  OTHER DEALINGS IN THE SOFTWARE.

"""The CCD fileformat is used by the CrysalisPro software (provided for free by Rigaku)
The main developper of CrysalisPro is Mathias Meyer. Thanks to him for providing the structure of the file.
This file contains the code to generate a mask-file.
"""

__authors__ = ["Jérôme Kieffer"]
__contact__ = "jerome.kieffer@esrf.eu"
__license__ = "MIT"
__copyright__ = "2022 ESRF"
__date__ = "16/12/2022"

import logging
logger = logging.getLogger(__name__)
import numpy
from .fabioimage import FabioImage, OrderedDict
from dataclasses import dataclass
from enum import Enum
import struct
# Some constants used in the file:

class CCD_FILEVERSION(Enum):
    VERS_1_1 = 0x00010001
    VERS_1_2 = 0x00010002
    VERS_1_3 = 0x00010003
    VERS_1_4 = 0x00010004
    VERS_1_5 = 0x00010005
    VERS_1_6 = 0x00010006
    VERS_1_7 = 0x00010007
    VERS_1_8 = 0x00010008
    VERS_1_9 = 0x00010009
    VERS_1_10 = 0x0001000a
    VERS_1_11 = 0x0001000b
    VERS_1_12 = 0x0001000c
    
    
CCD_FILEVERSION_VERS_HIGHEST =CCD_FILEVERSION.VERS_1_12

class CHIPCHARACTERISTICS_TREATMENT(Enum):
    IGNORE = 0
    REPLACE = 1
    AVERAGE = 2
    REPLACELEFT = 3
    REPLACERIGHT = 4
    AVERAGELEFTRIGHT = 5
    TREATMENT_REPLACETOP = 6
    REPLACEBOTTOM = 7
    AVERAGETOPBOTTOM = 8

class CHIPCHARACTERISTICS_POLYGONTYPE(Enum):
    TRIANGLE = 0
    RECTANGLE = 1
    POLYGON = 2
    MAXPOINTS = 6

class CHIPCHARACTERISTICS_SCINTILLATORID(Enum):
    NOTPRESENT = 0
    GREEN400 = 1
    LEXEL40 = 2
    LEXEL60 = 3
    LEXEL100 = 4
    RAREXMED = 5
    RAREXFINE = 6
    GREEN400_NEW = 7

CHIPCHARACTERISTICS_SCINTILLATORID_FIRST = CHIPCHARACTERISTICS_SCINTILLATORID.GREEN400
CHIPCHARACTERISTICS_SCINTILLATORID_LAST = CHIPCHARACTERISTICS_SCINTILLATORID.GREEN400_NEW

@dataclass
class ChipPoint:
    ix: int
    iy: int
    
    @classmethod
    def loads(cls, buffer):
        buffer_len = 4
        assert len(buffer)>=buffer_len
        return cls(*struct.unpack("<HH", buffer[:buffer_len]))

    def dumps(self):
        return struct.pack("<HH", self.ix, self.iy)

@dataclass
class ChipBadPoint:
    spt: ChipPoint
    sptreplace1:ChipPoint
    sptreplace2: ChipPoint
    itreatment :int

    @classmethod
    def loads(cls, buffer):
        buffer_len = 14
        assert len(buffer)>=buffer_len
        return cls(ChipPoint(buffer[:4]),
                   ChipPoint(buffer[4:8])
                   ChipPoint(buffer[8:12])
                   struct.unpack("<H", buffer[12:buffer_len]))

    def dumps(self):
        return spt.dumps() + \
            sptreplace1.dumps() + \
            sptreplace2.dumps() + \
            struct.pack("<H", self.itreatment)

@dataclass
class ChipBadRow:
    """ROW STARTX ENDX Y"""    
    sptstart: ChipPoint
    sptend: ChipPoint
    sptstartreplace:ChipPoint
    sptendreplace: ChipPoint
    itreatment :int

    @classmethod
    def loads(cls, buffer):
        buffer_len = 18
        assert len(buffer)>=buffer_len
        return cls(ChipPoint(buffer[:4]),
                   ChipPoint(buffer[4:8]),
                   ChipPoint(buffer[8:12]),
                   ChipPoint(buffer[12:16]),
                   struct.unpack("<H", buffer[16:buffer_len])[0])

    def dumps(self):
        return sptstart.dumps() + \
            sptend.dumps() + \
            sptstartreplace.dumps() + \
            sptendreplace.dumps() + \
            struct.pack("<H", self.itreatment)

@dataclass
class ChipBadColumn:
    """COLUMN X STARTY ENDY"""    
    sptstart: ChipPoint
    sptend: ChipPoint
    sptstartreplace:ChipPoint
    sptendreplace: ChipPoint
    itreatment :int
    ilowlimit: int
    ihighlimit: int

    @classmethod
    def loads(cls, buffer):
        buffer_len = 22
        assert len(buffer)>=buffer_len
        return cls(ChipPoint(buffer[:4]),
                   ChipPoint(buffer[4:8]),
                   ChipPoint(buffer[8:12]),
                   ChipPoint(buffer[12:16]),
                   *struct.unpack("<HHH", buffer[16:buffer_len]))

    def dumps(self):
        return sptstart.dumps() + \
            sptend.dumps() + \
            sptstartreplace.dumps() + \
            sptendreplace.dumps() + \
            struct.pack("<HHH", self.itreatment, self.ilowlimit, self.ihighlimit)

@dataclass
class ChipBadPolygon:
    itype:int
    ipoints: int
    iax: List[int]
    iay: List[int]

    @classmethod
    def loads(cls, buffer):
        buffer_len = 2*(2+2*CHIPCHARACTERISTICS_POLYGONTYPE.MAXPOINTS)
        assert len(buffer)>=buffer_len
        lst = struct.unpack("<HH"+"H"*2*CHIPCHARACTERISTICS_POLYGONTYPE.MAXPOINTS,
                            buffer[:buffer_len])
        return cls(lst[0], lst[1],
                   lst[2:2+CHIPCHARACTERISTICS_POLYGONTYPE.MAXPOINTS],
                   lst[2+CHIPCHARACTERISTICS_POLYGONTYPE.MAXPOINTS:],)

    def dumps(self):
        return struct.pack("<HH"+"H"*2*CHIPCHARACTERISTICS_POLYGONTYPE.MAXPOINTS,
                           self.itype, self.ipoints, *self.iax, *self.iay)

@dataclass
class ChipMachineFunction:
    """
    xl is log10 of true Xray intensity
    y=A * exp (B * xl)
    """
    iismachinefunction: int
    da_machinefct: float
    db_machinefct: float

    @classmethod
    def loads(cls, buffer):
        buffer_len = 2+8+8
        assert len(buffer)>=buffer_len
        lst = struct.unpack("<HH"+"H"*2*CHIPCHARACTERISTICS_POLYGONTYPE.MAXPOINTS,
                            buffer[:buffer_len])
        return cls(lst[0], lst[1],
                   lst[2:2+CHIPCHARACTERISTICS_POLYGONTYPE.MAXPOINTS],
                   lst[2+CHIPCHARACTERISTICS_POLYGONTYPE.MAXPOINTS:],)

    def dumps(self):
        return struct.pack("<HH"+"H"*2*CHIPCHARACTERISTICS_POLYGONTYPE.MAXPOINTS,
                           self.itype, self.ipoints, *self.iax, *self.iay)
    
@dataclass
class CcdCharacteristiscs:
    """Names are using the hugarian notation: the first letter describes the type
    
    strings are 256bytes long
    floats are 64bits
    integers are 16bits, probably unsigned
    """
    ddarkcurrentinADUpersec:float
    dreadnoiseinADU: float
    ccharacteristicsfil: str
    cccdproducer: str
    cccdchiptype: str
    cccdchipserial: str

    ibadpoints: int 
    pschipbadpoint: list
    ibadcolumns: int
    pschipbadcolumn: list
    ibadrows: int
    pschipbadrow: list

    ibadcolumns1x1: int
    pschipbadcolumn1x1: list
    ibadcolumns2x2: int
    struct chipbadcolumn_tag *pschipbadcolumn2x2;
    ibadcolumns4x4: int
    struct chipbadcolumn_tag *pschipbadcolumn4x4;

    //1X1 2X2 4X4 BAD ROWS
    SHORT ibadrows1x1: int
    struct chipbadrow_tag *pschipbadrow1x1;
    SHORT ibadrows2x2: int
    struct chipbadrow_tag *pschipbadrow2x2;
    SHORT ibadrows4x4: int
    struct chipbadrow_tag *pschipbadrow4x4;

    ctaperproducer: str
    ctapertype: str
    ctaperserial: str
    iisfip60origin: int
    ifip60xorigin: int
    ifip60yorigin: int
    inumofcornermasks: int
    iacornermaskx[4],
    iacornermasky[4];
    inumofglowingcornermasks: int
    iaglowingcornermaskx[4]
    iaglowingcornermasky[4]
    ibadpolygons: int
    pschipbadpolygon:list
    struct chipmachinefunction_tag schipmachinefunction;
    iisrepairprint: int
    iscintillatorid,iisscintillatorid: int
    dgain_cu:float
    dgain_mo:float

class CcdImage(FabioImage):
    """FabIO image class for CrysalisPro mask image

    Put some documentation here
    """

    DESCRIPTION = "Name of the file format"

    DEFAULT_EXTENSIONS = []

    def __init__(self, *arg, **kwargs):
        """
        Generic constructor
        """
        FabioImage.__init__(self, *arg, **kwargs)

    def _readheader(self, infile):
        """
        Read and decode the header of an image:

        :param infile: Opened python file (can be stringIO or bzipped file)
        """
        # list of header key to keep the order (when writing)
        self.header = self.check_header()

    def read(self, fname, frame=None):
        """
        Try to read image

        :param fname: name of the file
        :param frame: number of the frame
        """

        self.resetvals()
        with self._open(fname) as infile:
            self._readheader(infile)
            # read the image data and declare it

        shape = (50, 60)
        self.data = numpy.zeros(shape, dtype=self.uint16)
        # Nota: dim1, dim2, bytecode and bpp are properties defined by the dataset
        return self


# This is not compatibility with old code:
ccdimage = CcdImage
