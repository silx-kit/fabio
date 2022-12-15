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
__date__ = "15/12/2022"

import logging
logger = logging.getLogger(__name__)
import numpy
from .fabioimage import FabioImage, OrderedDict
from dataclasses import dataclass

# Some constants used in the file:

CCD_FILEVERSION_VERS_1_1 = 0x00010001
CCD_FILEVERSION_VERS_1_2 = 0x00010002
CCD_FILEVERSION_VERS_1_3 = 0x00010003
CCD_FILEVERSION_VERS_1_4 = 0x00010004
CCD_FILEVERSION_VERS_1_5 = 0x00010005
CCD_FILEVERSION_VERS_1_6 = 0x00010006
CCD_FILEVERSION_VERS_1_7 = 0x00010007
CCD_FILEVERSION_VERS_1_8 = 0x00010008
CCD_FILEVERSION_VERS_1_9 = 0x00010009
CCD_FILEVERSION_VERS_1_10 = 0x0001000a
CCD_FILEVERSION_VERS_1_11 = 0x0001000b
CCD_FILEVERSION_VERS_1_12 = 0x0001000c
CCD_FILEVERSION_VERS_HIGHEST =CCD_FILEVERSION_VERS_1_12

CHIPCHARACTERISTICS_TREATMENT = {"IGNORE":            0,
                                 "REPLACE":           1,
#define CHIPCHARACTERISTICS_TREATMENT_AVERAGE            2
#define CHIPCHARACTERISTICS_TREATMENT_REPLACELEFT        3
#define CHIPCHARACTERISTICS_TREATMENT_REPLACERIGHT        4
#define CHIPCHARACTERISTICS_TREATMENT_AVERAGELEFTRIGHT    5
#define CHIPCHARACTERISTICS_TREATMENT_REPLACETOP        6
#define CHIPCHARACTERISTICS_TREATMENT_REPLACEBOTTOM        7
#define CHIPCHARACTERISTICS_TREATMENT_AVERAGETOPBOTTOM    8
}

@dataclass
class CcdCharacteristics:
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
templateimage = TemplateImage
