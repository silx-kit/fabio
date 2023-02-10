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
__date__ = "10/02/2023"

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


CCD_FILEVERSION_VERS_HIGHEST = CCD_FILEVERSION.VERS_1_12


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
    ix: int = 0
    iy: int = 0
    SIZE = 4

    @classmethod
    def loads(cls, buffer):
        assert len(buffer) >= cls.SIZE
        return cls(*struct.unpack("<HH", buffer[:cls.SIZE]))

    def dumps(self):
        return struct.pack("<HH", self.ix, self.iy)


@dataclass
class ChipBadPoint:
    spt: ChipPoint
    sptreplace1:ChipPoint
    sptreplace2: ChipPoint
    itreatment:int = 0
    SIZE = 14

    @classmethod
    def loads(cls, buffer):
        assert len(buffer) >= cls.SIZE
        return cls(ChipPoint(buffer[:4]),
                   ChipPoint(buffer[4:8]),
                   ChipPoint(buffer[8:12]),
                   struct.unpack("<H", buffer[12:cls.SIZE]))

    def dumps(self):
        return  self.spt.dumps() + \
                self.sptreplace1.dumps() + \
                self.sptreplace2.dumps() + \
                struct.pack("<H", self.itreatment)


@dataclass
class ChipBadRow:
    """ROW STARTX ENDX Y"""
    sptstart: ChipPoint
    sptend: ChipPoint
    sptstartreplace:ChipPoint
    sptendreplace: ChipPoint
    itreatment:int
    SIZE = 18

    @classmethod
    def loads(cls, buffer):
        cls.SIZE = cls.SIZE
        assert len(buffer) >= cls.SIZE
        return cls(ChipPoint(buffer[:4]),
                   ChipPoint(buffer[4:8]),
                   ChipPoint(buffer[8:12]),
                   ChipPoint(buffer[12:16]),
                   struct.unpack("<H", buffer[16:cls.SIZE])[0])

    def dumps(self):
        return  self.sptstart.dumps() + \
                self.sptend.dumps() + \
                self.sptstartreplace.dumps() + \
                self.sptendreplace.dumps() + \
                struct.pack("<H", self.itreatment)


@dataclass
class ChipBadColumn:
    """COLUMN X STARTY ENDY"""
    sptstart: ChipPoint
    sptend: ChipPoint
    sptstartreplace:ChipPoint
    sptendreplace: ChipPoint
    itreatment:int
    ilowlimit: int
    ihighlimit: int
    SIZE = 22

    @classmethod
    def loads(cls, buffer):
        assert len(buffer) >= cls.SIZE
        return cls(ChipPoint(buffer[:4]),
                   ChipPoint(buffer[4:8]),
                   ChipPoint(buffer[8:12]),
                   ChipPoint(buffer[12:16]),
                   *struct.unpack("<HHH", buffer[16:cls.SIZE]))

    def dumps(self):
        return self.sptstart.dumps() + \
               self.sptend.dumps() + \
               self.sptstartreplace.dumps() + \
               self.sptendreplace.dumps() + \
               struct.pack("<HHH", self.itreatment, self.ilowlimit, self.ihighlimit)


@dataclass
class ChipBadPolygon:
    itype:int
    ipoints: int
    iax: list
    iay: list
    SIZE = 2 * (2 + 2 * CHIPCHARACTERISTICS_POLYGONTYPE.MAXPOINTS.value)

    @classmethod
    def loads(cls, buffer):
        assert len(buffer) >= cls.SIZE
        lst = struct.unpack("<HH" + "H"*2 * CHIPCHARACTERISTICS_POLYGONTYPE.MAXPOINTS.value,
                            buffer[:cls.SIZE])
        return cls(lst[0], lst[1],
                   lst[2:2 + CHIPCHARACTERISTICS_POLYGONTYPE.MAXPOINTS.value],
                   lst[2 + CHIPCHARACTERISTICS_POLYGONTYPE.MAXPOINTS.value:],)

    def dumps(self):
        for lst in (self.iax, self.iay):
            if len(lst) < CHIPCHARACTERISTICS_POLYGONTYPE.MAXPOINTS.value:
                lst += [0]*(CHIPCHARACTERISTICS_POLYGONTYPE.MAXPOINTS.value-len(lst))
        return struct.pack("<HH" + "H"*2 * CHIPCHARACTERISTICS_POLYGONTYPE.MAXPOINTS.value,
                           self.itype, self.ipoints, 
                           *self.iax[:CHIPCHARACTERISTICS_POLYGONTYPE.MAXPOINTS.value], 
                           *self.iay[:CHIPCHARACTERISTICS_POLYGONTYPE.MAXPOINTS.value])


@dataclass
class ChipMachineFunction:
    """
    xl is log10 of true Xray intensity
    y=A * exp (B * xl)
    """
    iismachinefunction: int = 0
    da_machinefct: float = 0.0
    db_machinefct: float = 0.0
    SIZE = 18

    @classmethod
    def loads(cls, buffer):
        assert len(buffer) >= cls.SIZE
        lst = struct.unpack("<Hdd",
                            buffer[:cls.SIZE])
        return cls(lst[0], lst[1], lst[2])

    def dumps(self):
        return struct.pack("<Hdd", self.iismachinefunction, self.da_machinefct, self.db_machinefct)


@dataclass
class CcdCharacteristiscs:
    """Names are using the hugarian notation: the first letter describes the type
    
    strings are 256bytes long
    floats are 64bits
    integers are 16bits, probably unsigned
    """
    dwversion: int = 0
    ddarkcurrentinADUpersec:float = 0.0
    dreadnoiseinADU: float = 0.0
    ccharacteristicsfil: str = "n/a"
    cccdproducer: str = "n/a"
    cccdchiptype: str = "n/a"
    cccdchipserial: str = "n/a"
    ctaperproducer: str = "n/a"
    ctapertype: str = "n/a"
    ctaperserial: str = "n/a"

    iisfip60origin: int = 0
    ifip60xorigin: int = 0
    ifip60yorigin: int = 0

    inumofcornermasks: int = 0
    iacornermaskx: list = tuple()
    iacornermasky:list = tuple()
    inumofglowingcornermasks: int = 0
    iaglowingcornermaskx: list = tuple()
    iaglowingcornermasky:list = tuple()

    ibadpolygons: int = 0
    pschipbadpolygon:list = tuple()

    ibadpoints: int = 0
    pschipbadpoint: list = tuple()

    ibadcolumns: int = 0
    pschipbadcolumn: list = tuple()
    ibadcolumns1x1: int = 0
    pschipbadcolumn1x1: list = tuple()
    ibadcolumns2x2: int = 0
    pschipbadcolumn2x2: list = tuple()
    ibadcolumns4x4: int = 0
    pschipbadcolumn4x4: list = tuple()

    ibadrows: int = 0
    pschipbadrow: list = tuple()

    iscintillatorid: int = 0
    # iisscintillatorid: int =0
    dgain_cu:float = 0.0
    dgain_mo:float = 0.0
    chipmachinefunction: ChipMachineFunction = ChipMachineFunction()

    ibadrows1x1: int = 0
    pschipbadrow1x1: list = tuple()
    ibadrows2x2: int = 0
    pschipbadrow2x2: list = tuple()
    ibadrows4x4: int = 0
    pschipbadrow4x4: list = tuple()

    def _clip_string(self):
        """Clip all strings to 256 chars"""
        for key in ("ccharacteristicsfil", "cccdproducer", "cccdchiptype", "cccdchipserial", "ctaperproducer", "ctapertype", "ctaperserial"):
            value = self.__getattribute__(key)
            l = len(value)
            if l>256:
                self.__setattr__(key, value[:256])

    @classmethod
    def read(cls, filename):
        """The the filename.ccd"""
        with open(filename, "rb") as f:
            bytestream = f.read()
        return cls.loads(bytestream)

    @classmethod
    def loads(cls, bytestream):
        ended = False
        length = len(bytestream)
        dico = {}
        if length > 1854:
            dico["dwversion"] = struct.unpack("I", bytestream[:4])[0]  # VERSION
            dico["ddarkcurrentinADUpersec"] = struct.unpack("d", bytestream[4:12])[0]  # DARK CURRENT IN ADU
            dico["dreadnoiseinADU"] = struct.unpack("d", bytestream[12:20])[0]  # READ NOSE IN ADU
            dico["ccharacteristicsfil"] = bytestream[20:276].decode().strip("\x00")  # CHARACTISTICS FILE NAME
            dico["cccdproducer"] = bytestream[276:532].decode().strip("\x00")  # PRODUCER
            dico["cccdchiptype"] = bytestream[532:788].decode().strip("\x00")  # CHIP TYPE
            dico["cccdchipserial"] = bytestream[788:1044].decode().strip("\x00")  # CHIP SERIAL
            dico["ctaperproducer"] = bytestream[1044:1300].decode().strip("\x00")  # TAPER PRODUCER
            dico["ctapertype"] = bytestream[1300:1556].decode().strip("\x00")  #  TAPER TYPE
            dico["ctaperserial"] = bytestream[1556:1812].decode().strip("\x00")  #  TAPER SERIAL
            dico["iisfip60origin"], dico["ifip60xorigin"], dico["ifip60yorigin"] = struct.unpack("HHH", bytestream[1812:1818])  # FIP60ORIGIN

            dico["inumofcornermasks"] = struct.unpack("H", bytestream[1818:1820])  # CORNER MASKS
            dico["iacornermaskx"] = struct.unpack("HHHH", bytestream[1820:1828])
            dico["iacornermasky"] = struct.unpack("HHHH", bytestream[1828:1836])

            dico["inumofglowingcornermasks"] = struct.unpack("H", bytestream[1836:1838])  # GLOWINGCORNER MASKS
            dico["iaglowingcornermaskx"] = struct.unpack("HHHH", bytestream[1838:1846])
            dico["iaglowingcornermasky"] = struct.unpack("HHHH", bytestream[1846:1854])
        else:
            ended = True
        # NUMBER OF BAD POLYGONS
        start = 1856
        if not ended and start <= length:
            try:
                dico["ibadpolygons"] = struct.unpack("H", bytestream[1854:1856])[0]
                polygons = dico["pschipbadpolygon"] = []
                for _ in range(dico["ibadpolygons"]):
                    polygons.append(ChipBadPolygon.loads(bytestream[start:]))
                    start += ChipBadPolygon.SIZE
            except AssertionError:
                ended = True
        # NUMBER OF BAD POINTS
        if not ended and start + 2 <= length:
            try:
                dico["ibadpoints"] = struct.unpack("H", bytestream[start:start + 2])[0]
                start += 2
                points = dico["pschipbadpoint"] = []
                for _ in range(dico["ibadpoints"]):  # LOOP OVER BAD POINTS
                    points.append(ChipBadPoint.loads(bytestream[start:]))
                    start += ChipBadPoint.SIZE
            except AssertionError:
                ended = True

        # NUMBER OF BAD COLS
        if not ended and start + 2 <= length:
            try:
                dico["ibadcolumns"] = struct.unpack("H", bytestream[start:start + 2])[0]
                start += 2
                columns = dico["pschipbadcolumn"] = []
                for _ in range(dico["ibadcolumns"]):  # LOOP OVER BAD COLS
                    columns.append(ChipBadColumn.loads(bytestream[start:]))
                    start += ChipBadColumn.SIZE
            except AssertionError:
                ended = True

        # NUMBER OF BAD COLS 1X1
        if not ended and start + 2 <= length:
            try:
                dico["ibadcolumns1x1"] = struct.unpack("H", bytestream[start:start + 2])[0]
                start += 2
                columns = dico["pschipbadcolumn1x1"] = []
                for _ in range(dico["ibadcolumns1x1"]):  # LOOP OVER BAD COLS
                    columns.append(ChipBadColumn.loads(bytestream[start:]))
                    start += ChipBadColumn.SIZE
            except AssertionError:
                ended = True

        # NUMBER OF BAD COLS 2X2
        if not ended and start + 2 <= length:
            try:
                dico["ibadcolumns2x2"] = struct.unpack("H", bytestream[start:start + 2])[0]
                start += 2
                columns = dico["pschipbadcolumn2x2"] = []
                for _ in range(dico["ibadcolumns2x2"]):  # LOOP OVER BAD COLS
                    columns.append(ChipBadColumn.loads(bytestream[start:]))
                    start += ChipBadColumn.SIZE
            except AssertionError:
                ended = True

        # NUMBER OF BAD COLS 4X4
        if not ended and start + 2 <= length:
            try:
                dico["ibadcolumns4x4"] = struct.unpack("H", bytestream[start:start + 2])[0]
                start += 2
                columns = dico["pschipbadcolumn4x4"] = []
                for _ in range(dico["ibadcolumns4x4"]):  # LOOP OVER BAD COLS
                    columns.append(ChipBadColumn.loads(bytestream[start:]))
                    start += ChipBadColumn.SIZE
            except AssertionError:
                ended = True

        # NUMBER OF BAD ROWS
        if not ended and start + 2 <= length:
            try:
                dico["ibadrows"] = struct.unpack("H", bytestream[start:start + 2])[0]
                start += 2
                columns = dico["pschipbadrow"] = []
                for _ in range(dico["ibadrows"]):  # LOOP OVER BAD COLS
                    columns.append(ChipBadRow.loads(bytestream[start:]))
                    start += ChipBadRow.SIZE
            except AssertionError:
                ended = True

        if not ended and start + 18 <= length:
            try:
                dico["iscintillatorid"] = struct.unpack("H", bytestream[start:start + 2])[0]  # SCINTILLATOR DESCRIPTION
                dico["dgain_mo"] = struct.unpack("d", bytestream[start + 2:start + 10])[0]  # GAINMO
                dico["dgain_cu"] = struct.unpack("d", bytestream[start + 10:start + 18])[0]  # GAINCU
                start += 18
                dico["chipmachinefunction"] = ChipMachineFunction.loads(bytestream[start:])  # IISMACHINEFUNCTION
                start += ChipMachineFunction.SIZE
            except AssertionError:
                ended = True

        # NUMBER OF BAD ROWS 1X1
        if not ended and start + 2 <= length:
            try:
                dico["ibadrows1x1"] = struct.unpack("H", bytestream[start:start + 2])[0]
                start += 2
                columns = dico["pschipbadrow1x1"] = []
                for _ in range(dico["ibadcolumns1x1"]):  # LOOP OVER BAD COLS
                    columns.append(ChipBadRow.loads(bytestream[start:]))
                    start += ChipBadRow.SIZE
            except AssertionError:
                ended = True

        # NUMBER OF BAD ROWS 2X2
        if not ended and start + 2 <= length:
            try:
                dico["ibadrows2x2"] = struct.unpack("H", bytestream[start:start + 2])[0]
                start += 2
                columns = dico["pschipbadrow2x2"] = []
                for _ in range(dico["ibadrows2x2"]):  # LOOP OVER BAD COLS
                    columns.append(ChipBadRow.loads(bytestream[start:]))
                    start += ChipBadRow.SIZE
            except AssertionError:
                ended = True

        # NUMBER OF BAD ROWS 4X4
        if not ended and start + 2 <= length:
            try:
                dico["ibadrows4x4"] = struct.unpack("H", bytestream[start:start + 2])[0]
                start += 2
                columns = dico["pschipbadrow4x4"] = []
                for _ in range(dico["ibadrows4x4"]):  # LOOP OVER BAD COLS
                    columns.append(ChipBadRow.loads(bytestream[start:]))
                    start += ChipBadRow.SIZE
            except AssertionError:
                ended = True

        self = cls(**dico)
        return self

    def save(self, filename):
        with open(filename, "wb")  as w:
            w.write(self.dumps())

    def dumps(self):
        """Dump the content of the struct as a bytestream."""
        buffer = bytearray(4096)
        end = 0
        # prepare the structure
        if not self.dwversion:
            self.dwversion = CCD_FILEVERSION_VERS_HIGHEST
        self._clip_string()
        self.ibadpolygons = len(self.pschipbadpolygon)
        self.ibadpoints = len(self.pschipbadpoint)
        for empty_4_tuple in ("iacornermaskx", "iacornermasky", 
                              "iaglowingcornermaskx", "iaglowingcornermasky"): 
            value = self.__getattribute__(empty_4_tuple)
            if len(value) == 0:
                self.__setattr__(empty_4_tuple, [0,0,0,0])

        # Some helper functions
        def record_str(key):
            value = self.__getattribute__(key)
            buffer[end:end+len(value)] = value.encode()
            return 256
        
        def record_struct(key, dtype):
            value = self.__getattribute__(key)
            size = struct.calcsize(dtype)
            if isinstance(value, (list, tuple)):
                buffer[end:end+size] = struct.pack(dtype, *value)
            else:
                buffer[end:end+size] = struct.pack(dtype, value)
            return size
        
        def record_object(key):
            value = self.__getattribute__(key)
            tmp = value.dumps()
            ltmp = len(tmp)
            buffer[end:end+ltmp] = tmp
            return ltmp
        
        def record_variable(key, subkey, dtype="H"):
            size = struct.calcsize(dtype)
            values = self.__getattribute__(subkey)
            nitems = len(values)
            self.__setattr__(key, nitems)
            buffer[end:end+size] = struct.pack(dtype, nitems)
            for i in values:
                tmp = i.dumps()
                ltmp = len(tmp)
                buffer[end+size:end+size+ltmp] = tmp
                size += ltmp
            return size
        
        
        end += record_struct("dwversion", "I") # VERSION
        end += record_struct("ddarkcurrentinADUpersec", "d") # DARK CURRENT IN ADU
        end += record_struct("dreadnoiseinADU", "d") # READ NOSE IN ADU
        end +=record_str("ccharacteristicsfil")
        end +=record_str("cccdproducer")
        end +=record_str("cccdchiptype")
        end +=record_str("cccdchipserial")
        end +=record_str("ctaperproducer")
        end +=record_str("ctapertype")
        end +=record_str("ctaperserial")
        end += record_struct("iisfip60origin", "H")
        end += record_struct("ifip60xorigin", "H")
        end += record_struct("ifip60yorigin", "H")
        end += record_struct("inumofcornermasks", "H")
        end += record_struct("iacornermaskx", "HHHH")
        end += record_struct("iacornermasky", "HHHH")
        end += record_struct("inumofglowingcornermasks", "H")
        end += record_struct("iaglowingcornermaskx", "HHHH")
        end += record_struct("iaglowingcornermasky", "HHHH")
        end += record_variable("ibadpolygons", "pschipbadpolygon")
        end += record_variable("ibadpoints", "pschipbadpoint")
        end += record_variable("ibadcolumns", "pschipbadcolumn")
        end += record_variable("ibadcolumns1x1", "pschipbadcolumn1x1")        
        end += record_variable("ibadcolumns2x2", "pschipbadcolumn2x2")
        end += record_variable("ibadcolumns4x4", "pschipbadcolumn4x4")
        end += record_variable("ibadrows", "pschipbadrow")
        end += record_struct("iscintillatorid", "H")
        end += record_struct("dgain_mo", "d")
        end += record_struct("dgain_cu", "d")
        end += record_object("chipmachinefunction")
        end += record_variable("ibadrows1x1", "pschipbadrow1x1")
        end += record_variable("ibadrows2x2", "pschipbadrow2x2")
        end += record_variable("ibadrows4x4", "pschipbadrow4x4")
        return bytes(buffer[:end])

class XcaliburImage(FabioImage):
    """FabIO image class for CrysalisPro mask image
    """

    DESCRIPTION = "Xcalibur binary struct of masked pixels"

    DEFAULT_EXTENSIONS = []

    def __init__(self, *arg, **kwargs):
        """
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

    def decompose(self, full=False):
        """Decompose a mask defined as a 2D binary image in 
        
        * vertical+horizontal gaps
        * rectangles
        * bad pixels 
        
        :param: full: deal only with gaps (False) or perform the complete analysis (True) 
        :return: CcdCharacteristiscs struct.
        """
        ccd = CcdCharacteristiscs(CCD_FILEVERSION_VERS_HIGHEST.value,
                                  pschipbadpolygon=[],
                                  pschipbadpoint=[])
        mask = numpy.array(self.data, dtype=bool)
        shape = mask.shape
        
        row_gaps = self._search_gap(mask, dim=1)
        col_gaps = self._search_gap(mask, dim=0)
        
        ccd.ibadpolygons = len(row_gaps)+len(col_gaps)
        ccd.pschipbadpolygon = []
        for gap in row_gaps:
            polygon = ChipBadPolygon(CHIPCHARACTERISTICS_POLYGONTYPE.RECTANGLE.value, 4,
                                     [0, shape[1]-1],[gap[0], gap[1]-1])
            ccd.pschipbadpolygon.append(polygon)
        for gap in col_gaps:
            polygon = ChipBadPolygon(CHIPCHARACTERISTICS_POLYGONTYPE.RECTANGLE.value, 4,
                                     [gap[0], gap[1]-1], [0, shape[0]-1])
            ccd.pschipbadpolygon.append(polygon)

        try:
            import pyFAI.ext.dynamic_rectangle
        except ImportError:
            logger.warning("PyFAI not available: only a coarse description of the mask is provided")
            full = False
        if not full:
            return ccd
        # Decompose detector into a set of modules, then extract patches of mask for each of them:
        c = 0
        for cg in col_gaps+[(self.shape[1], self.shape[1])]:
            r=0
            for rg in row_gaps+[(self.shape[0],self.shape[0])]:
                mm = mask[r:rg[0],c:cg[0]]
                if mm.size: 
                    rectangles = pyFAI.ext.dynamic_rectangle.decompose_mask(mm)
                    for rec in rectangles:
                        if rec.area == 1:
                            point = ChipPoint(c+rec.col, r+rec.row)
                            bad_point = ChipBadPoint(point, point, point, CHIPCHARACTERISTICS_TREATMENT.IGNORE.value)
                            ccd.ibadpoints+=1
                            ccd.pschipbadpoint.append(bad_point)
                        else:
                            ccd.ibadpolygons += 1
                            polygon = ChipBadPolygon(CHIPCHARACTERISTICS_POLYGONTYPE.RECTANGLE.value, 4,
                                                     [c+rec.col, c+rec.col+rec.width-1], 
                                                     [r+rec.row, r+rec.row+rec.height-1])
                            ccd.pschipbadpolygon.append(polygon)
                r = rg[1]
            c = cg[1]
        return ccd
        

    @staticmethod
    def _search_gap(mask, dim=0):
        
        shape = mask.shape
        m0 = numpy.sum(mask, axis=dim, dtype="int") == shape[dim]
        if m0.any():
            m0 = numpy.asarray(m0, "int8")
            d0=m0[1:]-m0[:-1]
            starts = numpy.where(d0==1)[0]
            stops = numpy.where(d0==-1)[0]
            if  (len(starts) == 0):
                starts = numpy.array([-1])
            if  (len(stops) == 0):
                stops = numpy.array([len(m0)-1])
            if (stops[0]<starts[0]):
                starts = numpy.concatenate(([-1], starts))
            if (stops[-1]<starts[-1]):
                stops = numpy.concatenate((stops, [len(m0)-1]))
            r0 = [ (start+1, stop+1) for start,stop  in zip(starts, stops)]
        else:
            r0 = []
        return r0


# This is for compatibility with old code:
xcaliburimage = XcaliburImage
