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

"""Reads Oxford Diffraction Sapphire 3 images

Authors:
........
* Henning O. Sorensen & Erik Knudsen:
  Center for Fundamental Research: Metal Structures in Four Dimensions;
  Risoe National Laboratory;
  Frederiksborgvej 399;
  DK-4000 Roskilde;
  email:erik.knudsen@risoe.dk
* Jon Wright, Jérôme Kieffer & Gaël Goret:
  European Synchrotron Radiation Facility;
  Grenoble (France)

"""

__contact__ = "Jerome.Kieffer@esrf.fr"
__license__ = "MIT"
__copyright__ = "Jérôme Kieffer"
__date__ = "12/12/2022"

import time
import logging
import struct
logger = logging.getLogger(__name__)
import numpy
from numpy import rad2deg, deg2rad
from .fabioimage import FabioImage
from .compression import decTY1, compTY1
from .fabioutils import to_str

DETECTOR_TYPES = {0: 'Sapphire/KM4CCD (1x1: 0.06mm, 2x2: 0.12mm)',
                  1: 'Sapphire2-Kodak (1x1: 0.06mm, 2x2: 0.12mm)',
                  2: 'Sapphire3-Kodak (1x1: 0.03mm, 2x2: 0.06mm, 4x4: 0.12mm)',
                  3: 'Onyx-Kodak (1x1: 0.06mm, 2x2: 0.12mm, 4x4: 0.24mm)',
                  4: 'Unknown Oxford diffraction detector',
                  7: 'Pilatus 300K-Dectris'}

DEFAULT_HEADERS = {'Header Version': 'OD SAPPHIRE  3.0',
                   'Compression': "TY1",
                   'Header Size In Bytes': 5120,
                   "ASCII Section size in Byte": 256,
                   "General Section size in Byte": 512,
                   "Special Section size in Byte": 768,
                   "KM4 Section size in Byte": 1024,
                   "Statistic Section in Byte": 512,
                   "History Section in Byte": 2048,
                   'NSUPPLEMENT': 0
                   }


class OxdImage(FabioImage):
    """
    Oxford Diffraction Sapphire 3 images reader/writer class

    Note: We assume the binary format is alway little-endian, is this True ?
    """

    DESCRIPTION = "Oxford Diffraction Sapphire 3 file format"

    DEFAULT_EXTENSIONS = ["img"]

    def _readheader(self, infile):

        infile.seek(0)

        # Ascii header part 256 byes long
        self.header['Header Version'] = to_str(infile.readline()[:-2])
        block = infile.readline()
        self.header['Compression'] = to_str(block[12:15])
        block = infile.readline()
        self.header['NX'] = int(block[3:7])
        self.header['NY'] = int(block[11:15])
        self.header['OI'] = int(block[19:26])
        self.header['OL'] = int(block[30:37])
        block = infile.readline()
        self.header['Header Size In Bytes'] = int(block[8:15])
        self.header['General Section size in Byte'] = int(block[19:26])
        self.header['Special Section size in Byte'] = int(block[30:37])
        self.header['KM4 Section size in Byte'] = int(block[41:48])
        self.header['Statistic Section in Byte'] = int(block[52:59])
        self.header['History Section in Byte'] = int(block[63:])
        block = infile.readline()
        self.header['NSUPPLEMENT'] = int(block[12:19])
        block = infile.readline()
        self.header['Time'] = to_str(block[5:29])

        header_version = float(self.header['Header Version'].split()[2])
        if header_version < 4.0:
            # for all our test files with header version 3.0
            # ascii_section_size == 256
            # but that's a legacy code
            ascii_section_size = self.header['Header Size In Bytes'] - (
                self.header['General Section size in Byte'] +
                self.header['Special Section size in Byte'] +
                self.header['KM4 Section size in Byte'] +
                self.header['Statistic Section in Byte'] +
                self.header['History Section in Byte'])
        else:
            ascii_section_size = DEFAULT_HEADERS["ASCII Section size in Byte"]
        self.header["ASCII Section size in Byte"] = ascii_section_size

        # Skip to general section (NG) 512 byes long <<<<<<"
        infile.seek(self.header["ASCII Section size in Byte"])
        block = infile.read(self.header['General Section size in Byte'])
        self.header['Binning in x'] = struct.unpack("<H", block[0:2])[0]
        self.header['Binning in y'] = struct.unpack("<H", block[2:4])[0]
        self.header['Detector size x'] = struct.unpack("<H", block[22:24])[0]
        self.header['Detector size y'] = struct.unpack("<H", block[24:26])[0]
        self.header['Pixels in x'] = struct.unpack("<H", block[26:28])[0]
        self.header['Pixels in y'] = struct.unpack("<H", block[28:30])[0]
        self.header['No of pixels'] = struct.unpack("<I", block[36:40])[0]

        # Speciel section (NS) 768 bytes long
        block = infile.read(self.header['Special Section size in Byte'])
        self.header['Gain'] = struct.unpack("<d", block[56:64])[0]
        self.header['Overflows flag'] = struct.unpack("<h", block[464:466])[0]
        self.header['Overflow after remeasure flag'] = struct.unpack("<h", block[466:468])[0]
        self.header['Overflow threshold'] = struct.unpack("<i", block[472:476])[0]
        self.header['Exposure time in sec'] = struct.unpack("<d", block[480:488])[0]
        self.header['Overflow time in sec'] = struct.unpack("<d", block[488:496])[0]
        self.header['Monitor counts of raw image 1'] = struct.unpack("<i", block[528:532])[0]
        self.header['Monitor counts of raw image 2'] = struct.unpack("<i", block[532:536])[0]
        self.header['Monitor counts of overflow raw image 1'] = struct.unpack("<i", block[536:540])[0]
        self.header['Monitor counts of overflow raw image 2'] = struct.unpack("<i", block[540:544])[0]
        self.header['Unwarping'] = struct.unpack("<i", block[544:548])[0]
        self.header['Detector type'] = DETECTOR_TYPES[struct.unpack("<i", block[548:552])[0]]
        self.header['Real pixel size x (mm)'] = struct.unpack("<d", block[568:576])[0]
        self.header['Real pixel size y (mm)'] = struct.unpack("<d", block[576:584])[0]

        # KM4 goniometer section (NK) 1024 bytes long
        block = infile.read(self.header['KM4 Section size in Byte'])
        # Spatial correction file
        self.header['Spatial correction file'] = to_str(block[26:272].strip(b"\x00"))
        self.header['Spatial correction file date'] = to_str(block[0:26].strip(b"\x00"))
        # Angles are in steps due to stepper motors - conversion factor RAD
        # angle[0] = omega, angle[1] = theta, angle[2] = kappa, angle[3] = phi,
        start_angles_step = numpy.frombuffer(block[284:304], numpy.int32)
        end_angles_step = numpy.frombuffer(block[324:344], numpy.int32)
        step2rad = numpy.frombuffer(block[368:408], numpy.float64)
        zero_correction_soft_step = numpy.frombuffer(block[512:532], numpy.int32)
        if not numpy.little_endian:
            start_angles_step.byteswap(True)
            end_angles_step.byteswap(True)
            step2rad.byteswap(True)
            zero_correction_soft_step.byteswap(True)
        step_angles_deg = rad2deg(step2rad)
        # calc angles
        start_angles_deg = start_angles_step * step_angles_deg
        end_angles_deg = end_angles_step * step_angles_deg
        self.header['Omega start in deg'] = start_angles_deg[0]
        self.header['Theta start in deg'] = start_angles_deg[1]
        self.header['Kappa start in deg'] = start_angles_deg[2]
        self.header['Phi start in deg'] = start_angles_deg[3]
        self.header['Omega end in deg'] = end_angles_deg[0]
        self.header['Theta end in deg'] = end_angles_deg[1]
        self.header['Kappa end in deg'] = end_angles_deg[2]
        self.header['Phi end in deg'] = end_angles_deg[3]
        self.header['Omega step in deg'] = step_angles_deg[0]
        self.header['Theta step in deg'] = step_angles_deg[1]
        self.header['Kappa step in deg'] = step_angles_deg[2]
        self.header['Phi step in deg'] = step_angles_deg[3]

        zero_correction_soft_deg = zero_correction_soft_step * step_angles_deg
        self.header['Omega zero corr. in deg'] = zero_correction_soft_deg[0]
        self.header['Theta zero corr. in deg'] = zero_correction_soft_deg[1]
        self.header['Kappa zero corr. in deg'] = zero_correction_soft_deg[2]
        self.header['Phi zero corr. in deg'] = zero_correction_soft_deg[3]
        # Beam rotation about e2,e3
        self.header['Beam rot in deg (e2)'] = struct.unpack("<d", block[552:560])[0]
        self.header['Beam rot in deg (e3)'] = struct.unpack("<d", block[560:568])[0]
        # Wavelenghts alpha1, alpha2, beta
        self.header['Wavelength alpha1'] = struct.unpack("<d", block[568:576])[0]
        self.header['Wavelength alpha2'] = struct.unpack("<d", block[576:584])[0]
        self.header['Wavelength alpha'] = struct.unpack("<d", block[584:592])[0]
        self.header['Wavelength beta'] = struct.unpack("<d", block[592:600])[0]

        # Detector tilts around e1,e2,e3 in deg
        self.header['Detector tilt e1 in deg'] = struct.unpack("<d", block[640:648])[0]
        self.header['Detector tilt e2 in deg'] = struct.unpack("<d", block[648:656])[0]
        self.header['Detector tilt e3 in deg'] = struct.unpack("<d", block[656:664])[0]

        # Beam center
        self.header['Beam center x'] = struct.unpack("<d", block[664:672])[0]
        self.header['Beam center y'] = struct.unpack("<d", block[672:680])[0]
        # Angle (alpha) between kappa rotation axis and e3 (ideally 50 deg)
        self.header['Alpha angle in deg'] = struct.unpack("<d", block[680:688])[0]
        # Angle (beta) between phi rotation axis and e3 (ideally 0 deg)
        self.header['Beta angle in deg'] = struct.unpack("<d", block[688:696])[0]

        # Detector distance
        self.header['Distance in mm'] = struct.unpack("<d", block[712:720])[0]
        # Statistics section (NS) 512 bytes long
        block = infile.read(self.header['Statistic Section in Byte'])
        self.header['Stat: Min '] = struct.unpack("<i", block[0:4])[0]
        self.header['Stat: Max '] = struct.unpack("<i", block[4:8])[0]
        self.header['Stat: Average '] = struct.unpack("<d", block[24:32])[0]
        self.header['Stat: Stddev '] = numpy.sqrt(struct.unpack("<d", block[32:40])[0])
        self.header['Stat: Skewness '] = struct.unpack("<d", block[40:48])[0]

        # History section (NH) 2048 bytes long
        block = infile.read(self.header['History Section in Byte'])
        self.header['Flood field image'] = to_str(block[99:126].strip(b"\x00"))

    def read(self, fname, frame=None):
        """
        Read in header into self.header and
            the data   into self.data
        """
        self.header = self.check_header()
        self.resetvals()
        with self._open(fname) as infile:
            self._readheader(infile)

            infile.seek(self.header['Header Size In Bytes'])

            # Compute image size
            try:
                dim1 = int(self.header['NX'])
                dim2 = int(self.header['NY'])
                self._shape = dim2, dim1
            except (ValueError, KeyError):
                raise IOError("Oxford  file %s is corrupted, cannot read it" % str(fname))

            if self.header['Compression'] == 'TY1':
                logger.debug("Compressed with the KM4CCD compression")
                raw8 = infile.read(dim1 * dim2)
                raw16 = None
                raw32 = None
                if self.header['OI'] > 0:
                    raw16 = infile.read(self.header['OI'] * 2)
                if self.header['OL'] > 0:
                    raw32 = infile.read(self.header['OL'] * 4)

                # endianess is handled at the decompression level
                raw_data = decTY1(raw8, raw16, raw32)
            elif self.header['Compression'] == 'TY5':
                logger.info("Compressed with the TY5 compression")
                dtype = numpy.dtype(numpy.int8)
                raw8 = infile.read(dim1 * dim2)

                if self.header['OI'] > 0:
                    self.raw16 = infile.read(self.header['OI'] * 2)
                else:
                    self.raw16 = b""
                if self.header['OL'] > 0:
                    self.raw32 = infile.read(self.header['OL'] * 4)
                else:
                    self.raw32 = b""
                self.rest = infile.read()
                self.blob = raw8 + self.raw16 + self.raw32 + self.rest
                raw_data = self.dec_TY5(raw8 + self.raw16 + self.raw32)
            else:
                dtype = numpy.dtype(numpy.int32)
                nbytes = dim1 * dim2 * dtype.itemsize
                raw_data = numpy.frombuffer(infile.read(nbytes), dtype).copy()
                # Always assume little-endian on the disk
                if not numpy.little_endian:
                    raw_data.byteswap(True)

        logger.debug('OVER_SHORT2: %s', raw_data.dtype)
        logger.debug("%s" % (raw_data < 0).sum())
        logger.debug("BYTECODE: %s", raw_data.dtype.type)
        self.data = raw_data.reshape((dim2, dim1))
        self._dtype = None
        return self

    def _writeheader(self):
        """
        :return: a string containing the header for Oxford images
        """
        linesep = "\r\n"
        for key in DEFAULT_HEADERS:
            if key not in self.header:
                self.header[key] = DEFAULT_HEADERS[key]

        if "NX" not in self.header.keys() or "NY" not in self.header.keys():
            dim2, dim1 = self.shape
            self.header['NX'] = dim1
            self.header['NY'] = dim2
        ascii_headers = [self.header['Header Version'],
                         "COMPRESSION=%s (%5.1f)" % (self.header["Compression"], self.getCompressionRatio()),
                         "NX=%4i NY=%4i OI=%7i OL=%7i " % (self.header["NX"], self.header["NY"], self.header["OI"], self.header["OL"]),
                         "NHEADER=%7i NG=%7i NS=%7i NK=%7i NS=%7i NH=%7i" % (self.header['Header Size In Bytes'],
                                                                             self.header['General Section size in Byte'],
                                                                             self.header['Special Section size in Byte'],
                                                                             self.header['KM4 Section size in Byte'],
                                                                             self.header['Statistic Section in Byte'],
                                                                             self.header['History Section in Byte']),
                         "NSUPPLEMENT=%7i" % (self.header["NSUPPLEMENT"])]
        if "Time" in self.header:
            ascii_headers.append("TIME=%s" % self.header["Time"])
        else:

            ascii_headers.append("TIME=%s" % time.ctime())

        header = (linesep.join(ascii_headers)).ljust(256).encode("ASCII")

        NG = Section(self.header['General Section size in Byte'], self.header)
        NG.setData('Binning in x', 0, numpy.uint16)
        NG.setData('Binning in y', 2, numpy.uint16)
        NG.setData('Detector size x', 22, numpy.uint16)
        NG.setData('Detector size y', 24, numpy.uint16)
        NG.setData('Pixels in x', 26, numpy.uint16)
        NG.setData('Pixels in y', 28, numpy.uint16)
        NG.setData('No of pixels', 36, numpy.uint32)
        header += NG.__repr__()

        NS = Section(self.header['Special Section size in Byte'], self.header)
        NS.setData('Gain', 56, numpy.float64)
        NS.setData('Overflows flag', 464, numpy.int16)
        NS.setData('Overflow after remeasure flag', 466, numpy.int16)
        NS.setData('Overflow threshold', 472, numpy.int32)
        NS.setData('Exposure time in sec', 480, numpy.float64)
        NS.setData('Overflow time in sec', 488, numpy.float64)
        NS.setData('Monitor counts of raw image 1', 528, numpy.int32)
        NS.setData('Monitor counts of raw image 2', 532, numpy.int32)
        NS.setData('Monitor counts of overflow raw image 1', 536, numpy.int32)
        NS.setData('Monitor counts of overflow raw image 2', 540, numpy.int32)
        NS.setData('Unwarping', 544, numpy.int32)
        if 'Detector type' in self.header:
            for key, value in DETECTOR_TYPES.items():
                if value == self.header['Detector type']:
                    NS.setData(None, 548, numpy.int32, default=key)
        NS.setData('Real pixel size x (mm)', 568, numpy.float64)
        NS.setData('Real pixel size y (mm)', 576, numpy.float64)
        header += NS.__repr__()

        KM = Section(self.header['KM4 Section size in Byte'], self.header)
        KM.setData('Spatial correction file date', 0, "|S26")
        KM.setData('Spatial correction file', 26, "|S246")
        # Angles are in steps due to stepper motors - conversion factor RAD
        # angle[0] = omega, angle[1] = theta, angle[2] = kappa, angle[3] = phi,
        if self.header.get('Omega step in deg', None):
            KM.setData(None, 368, numpy.float64, deg2rad(self.header["Omega step in deg"]))
            if self.header.get('Omega start in deg', None):
                KM.setData(None, 284, numpy.int32, self.header["Omega start in deg"] / self.header["Omega step in deg"])
            if self.header.get('Omega end in deg', None):
                KM.setData(None, 324, numpy.int32, self.header["Omega end in deg"] / self.header["Omega step in deg"])
            if self.header.get('Omega zero corr. in deg', None):
                KM.setData(None, 512, numpy.int32, self.header['Omega zero corr. in deg'] / self.header["Omega step in deg"])

        if self.header.get('Theta step in deg', None):
            KM.setData(None, 368 + 8, numpy.float64, deg2rad(self.header["Theta step in deg"]))
            if self.header.get('Theta start in deg', None):
                KM.setData(None, 284 + 4, numpy.int32, self.header["Theta start in deg"] / self.header["Theta step in deg"])
            if self.header.get('Theta end in deg', None):
                KM.setData(None, 324 + 4, numpy.int32, self.header["Theta end in deg"] / self.header["Theta step in deg"])
            if self.header.get('Theta zero corr. in deg', None):
                KM.setData(None, 512 + 4, numpy.int32, self.header['Theta zero corr. in deg'] / self.header["Theta step in deg"])

        if self.header.get('Kappa step in deg', None):
            KM.setData(None, 368 + 16, numpy.float64, deg2rad(self.header["Kappa step in deg"]))
            if self.header.get('Kappa start in deg', None):
                KM.setData(None, 284 + 8, numpy.int32, self.header["Kappa start in deg"] / self.header["Kappa step in deg"])
            if self.header.get('Kappa end in deg', None):
                KM.setData(None, 324 + 8, numpy.int32, self.header["Kappa end in deg"] / self.header["Kappa step in deg"])
            if self.header.get('Kappa zero corr. in deg', None):
                KM.setData(None, 512 + 8, numpy.int32, self.header['Kappa zero corr. in deg'] / self.header["Kappa step in deg"])

        if self.header.get('Phi step in deg', None):
            KM.setData(None, 368 + 24, numpy.float64, deg2rad(self.header["Phi step in deg"]))
            if self.header.get('Phi start in deg', None):
                KM.setData(None, 284 + 12, numpy.int32, self.header["Phi start in deg"] / self.header["Phi step in deg"])
            if self.header.get('Phi end in deg', None):
                KM.setData(None, 324 + 12, numpy.int32, self.header["Phi end in deg"] / self.header["Phi step in deg"])
            if self.header.get('Phi zero corr. in deg', None):
                KM.setData(None, 512 + 12, numpy.int32, self.header['Phi zero corr. in deg'] / self.header["Phi step in deg"])

        # Beam rotation about e2,e3
        KM.setData('Beam rot in deg (e2)', 552, numpy.float64)
        KM.setData('Beam rot in deg (e3)', 560, numpy.float64)
        # Wavelenghts alpha1, alpha2, beta
        KM.setData('Wavelength alpha1', 568, numpy.float64)
        KM.setData('Wavelength alpha2', 576, numpy.float64)
        KM.setData('Wavelength alpha', 584, numpy.float64)
        KM.setData('Wavelength beta', 592, numpy.float64)

        # Detector tilts around e1,e2,e3 in deg
        KM.setData('Detector tilt e1 in deg', 640, numpy.float64)
        KM.setData('Detector tilt e2 in deg', 648, numpy.float64)
        KM.setData('Detector tilt e3 in deg', 656, numpy.float64)

        # Beam center
        KM.setData('Beam center x', 664, numpy.float64)
        KM.setData('Beam center y', 672, numpy.float64)
        # Angle (alpha) between kappa rotation axis and e3 (ideally 50 deg)
        KM.setData('Alpha angle in deg', 680, numpy.float64)
        # Angle (beta) between phi rotation axis and e3 (ideally 0 deg)
        KM.setData('Beta angle in deg', 688, numpy.float64)

        # Detector distance
        KM.setData('Distance in mm', 712, numpy.float64)
        header += KM.__repr__()

        SS = Section(self.header['Statistic Section in Byte'], self.header)
        SS.setData('Stat: Min ', 0, numpy.int32)
        SS.setData('Stat: Max ', 4, numpy.int32)
        SS.setData('Stat: Average ', 24, numpy.float64)
        if self.header.get('Stat: Stddev ', None):
            SS.setData(None, 32, numpy.float64, self.header['Stat: Stddev '] ** 2)
        SS.setData('Stat: Skewness ', 40, numpy.float64)
        header += SS.__repr__()

        HS = Section(self.header['History Section in Byte'], self.header)
        HS.setData('Flood field image', 99, "|S27")
        header += HS.__repr__()

        return header

    def write(self, fname):
        """Write Oxford diffraction images: this is still beta
        Only TY1 compressed images is currently possible
        :param fname: output filename
        """
        if self.header.get("Compression") != "TY1":
            logger.warning("Enforce TY1 compression")
            self.header["Compression"] = "TY1"

        datablock8, datablock16, datablock32 = compTY1(self.data)
        self.header["OI"] = len(datablock16) // 2
        self.header["OL"] = len(datablock32) // 4
        with self._open(fname, mode="wb") as outfile:
            outfile.write(self._writeheader())
            outfile.write(datablock8)
            outfile.write(datablock16)
            outfile.write(datablock32)

    def getCompressionRatio(self):
        "calculate the compression factor obtained vs raw data"
        return 100.0 * (self.data.size + 2 * self.header["OI"] + 4 * self.header["OL"]) / (self.data.size * 4)

    @staticmethod
    def checkData(data=None):
        if data is None:
            return None
        else:
            return data.astype(int)

    def dec_TY5(self, stream):
        """
        Attempt to decode TY5 compression scheme

        :param stream: input stream
        :return: 1D array with data
        """
        logger.info("TY5 decompression is slow for now")
        array_size = self._shape[0] * self._shape[1]
        stream_size = len(stream)
        data = numpy.zeros(array_size)
        raw = numpy.frombuffer(stream, dtype=numpy.uint8)
        pos_inp = pos_out = current = ex1 = ex2 = 0

        dim2 = self._shape[0]
        while pos_inp < stream_size and pos_out < array_size:
            if pos_out % dim2 == 0:
                last = 0
            else:
                last = current
            value = raw[pos_inp]
            if value < 254:
                # this is the normal case
                # 1 bytes encode one pixel
                current = last + value - 127
                pos_inp += 1
            elif value == 254:
                ex1 += 1
                # this is the special case 1:
                # if the marker 254 is found the next 2 bytes encode one pixel
                value = raw[pos_inp + 1:pos_inp + 3].view(numpy.int16)
                if not numpy.little_endian:
                    value = value.byteswap(True)
                current = last + value[0]
                pos_inp += 3

            elif value == 255:
                # this is the special case 2:
                # if the marker 255 is found the next 4 bytes encode one pixel
                ex2 += 1
                logger.info('special case 32 bits.')
                value = raw[pos_inp + 1:pos_inp + 5].view(numpy.int32)
                if not numpy.little_endian:
                    value = value.byteswap(True)
                current = last + value[0]
                pos_inp += 5
            data[pos_out] = current
            pos_out += 1

        logger.info("TY5: Exception: 16bits: %s, 32bits: %s", ex1, ex2)
        return data


OXDimage = OxdImage


class Section(object):
    """
    Small helper class for writing binary headers
    """

    def __init__(self, size, dictHeader):
        """
        :param size: size of the header section in bytes
        :param dictHeader: headers of the image
        """
        self.size = size
        self.header = dictHeader
        self.lstChr = bytearray(size)
        self._dictSize = {}

    def __repr__(self):
        return bytes(self.lstChr)

    def getSize(self, dtype):
        if dtype not in self._dictSize:
            self._dictSize[dtype] = len(numpy.zeros(1, dtype=dtype).tobytes())
        return self._dictSize[dtype]

    def setData(self, key, offset, dtype, default=None):
        """
        :param offset: int, starting position in the section
        :param key: name of the header key
        :param dtype: type of the data to insert (defines the size!)
        """
        if key in self.header:
            value = self.header[key]
        elif key in DEFAULT_HEADERS:
            value = DEFAULT_HEADERS[key]
        else:
            value = default
        if value is None:
            value = b"\x00" * self.getSize(dtype)
        elif numpy.little_endian:
            value = numpy.array(value).astype(dtype).tobytes()
        else:
            value = numpy.array(value).astype(dtype).byteswap().tobytes()
        self.lstChr[offset:offset + self.getSize(dtype)] = value
