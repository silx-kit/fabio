# coding: utf-8
#
#    Project: X-ray image reader
#             https://github.com/silx-kit/fabio
#
#    Copyright (C) 2016 Univeristy Köln, Germany
#
#    Principal author:       Clemens Prescher (c.prescher@uni-koeln.de)
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

"""Princeton instrument SPE image reader for FabIO


"""

__authors__ = ["Clemens Prescher"]
__contact__ = "c.prescher@uni-koeln.de"
__license__ = "MIT"
__copyright__ = "Clemens Prescher"
__date__ = "09/02/2023"

import logging

logger = logging.getLogger(__name__)

import datetime
from xml.dom.minidom import parseString

import numpy as np
from numpy.polynomial.polynomial import polyval

from .fabioimage import FabioImage


class SpeImage(FabioImage):
    """FabIO image class for Images for Princeton/SPE detector

    Put some documentation here
    """
    DATA_TYPES = {0: np.float32,
                  1: np.int32,
                  2: np.int16,
                  3: np.uint16}

    DESCRIPTION = "Princeton instrument SPE file format"

    DEFAULT_EXTENSIONS = ["spe"]

    def _readheader(self, infile):
        """
        Read and decode the header of an image:

        :param infile: Opened python file (can be stringIO or bipped file)
        """

        self.header['version'] = self._get_version(infile)

        self.header['data_type'] = self._read_at(infile, 108, 1, np.uint16)[0]
        self.header['x_dim'] = int(self._read_at(infile, 42, 1, np.int16)[0])
        self.header['y_dim'] = int(self._read_at(infile, 656, 1, np.int16)[0])
        self.header['num_frames'] = self._read_at(infile, 1446, 1, np.int32)[0]

        if self.header['version'] == 2:
            self.header['time'] = self._read_date_time_from_header(infile)
            self.header['x_calibration'] = self._read_calibration_from_header(infile)
            self.header['exposure_time'] = self._read_at(infile, 10, 1, np.float32)[0]
            self.header['detector'] = 'unspecified'
            self.header['grating'] = str(self._read_at(infile, 650, 1, np.float32)[0])
            self.header['center_wavelength'] = float(self._read_at(infile, 72, 1, np.float32)[0])
            # # self._read_roi_from_header()
            # self._read_num_frames_from_header()
            # self._read_num_combined_frames_from_header()
        elif self.header['version'] == 3:
            xml_string = self._get_xml_string(infile)
            dom = self._create_dom_from_xml(xml_string)
            self.header['time'] = self._read_date_time_from_dom(dom)
            self.header['roi'] = self._read_roi_from_dom(dom)
            self.header['x_calibration'] = self._read_calibration_from_dom(dom)
            self.header['exposure_time'] = self._read_exposure_from_dom(dom)
            self.header['detector'] = self._read_detector_from_dom(dom)
            self.header['grating'] = self._read_grating_from_dom(dom, infile)
            self.header['center_wavelength'] = self._read_center_wavelength_from_dom(dom, infile)

        self.header = self.check_header(self.header)

    def read(self, fname, frame=None):
        """
        try to read image
        :param fname: name of the file
        :param frame:
        """

        self.resetvals()

        with self._open(fname, 'rb') as infile:
            self._readheader(infile)
            # read the image data and declare
            self.data = self._read_data(infile, frame)

        return self

    def _get_version(self, infile):
        self.xml_offset = self._read_at(infile, 678, 1, np.int64)[0]
        if self.xml_offset == 0:
            return 2
        else:
            return 3

    def _read_date_time_from_header(self, infile):
        """Reads the collection time from the header into the date_time field"""
        raw_date = self._read_at(infile, 20, 9, np.int8)
        raw_time = self._read_at(infile, 172, 6, np.int8)
        str_date = ''.join([chr(i) for i in raw_date])
        str_date += ''.join([chr(i) for i in raw_time])
        date_time = datetime.datetime.strptime(str_date, "%d%b%Y%H%M%S")
        return date_time.strftime("%m/%d/%Y %H:%M:%S")

    def _read_date_time_from_dom(self, dom):
        """Reads the time of collection and saves it date_time field"""
        date_time_str = dom.getElementsByTagName('Origin')[0].getAttribute('created')
        try:
            date_time = datetime.datetime.strptime(date_time_str[:-7], "%Y-%m-%dT%H:%M:%S.%f")
            return date_time.strftime("%m/%d/%Y %H:%M:%S.%f")
        except ValueError:
            date_time = datetime.datetime.strptime(date_time_str[:-6], "%Y-%m-%dT%H:%M:%S")
            return date_time.strftime("%m/%d/%Y %H:%M:%S")

    def _read_calibration_from_header(self, infile):
        """Reads the calibration from the header into the x_calibration field"""
        x_polynocoeff = self._read_at(infile, 3263, 6, np.double)
        x_val = np.arange(self.header['x_dim']) + 1
        return np.array(polyval(x_val, x_polynocoeff))

    def _read_calibration_from_dom(self, dom):
        """Reads the x calibration of the image from the xml footer and saves
        it in the x_calibration field"""
        spe_format = dom.childNodes[0]
        calibrations = spe_format.getElementsByTagName('Calibrations')[0]
        wavelengthmapping = calibrations.getElementsByTagName('WavelengthMapping')[0]
        wavelengths = wavelengthmapping.getElementsByTagName('Wavelength')[0]
        wavelength_values = wavelengths.childNodes[0]
        x_calibration = np.array([float(i) for i in wavelength_values.toxml().split(',')])
        return x_calibration[self.header['roi'][0]:self.header['roi'][1]]

    def _read_num_frames_from_header(self, infile):
        self.num_frames = self._read_at(infile, 1446, 1, np.int32)[0]

    def _get_xml_string(self, infile):
        """Reads out the xml string from the file end"""
        if "size" in dir(infile):
            size = infile.size
        elif "measure_size" in dir(infile):
            size = infile.measure_size()
        else:
            raise RuntimeError("Unable to guess the actual size of the file")
        xml_size = size - self.xml_offset
        xml = self._read_at(infile, self.xml_offset, xml_size, np.byte)
        return ''.join([chr(i) for i in xml])
        # if self.debug:
        #     fid = open(self.filename + '.xml', 'w')
        #     for line in self.xml_string:
        #         fid.write(line)
        #     fid.close()

    def _create_dom_from_xml(self, xml_string):
        """Creates a DOM representation of the xml footer and saves it in the
        dom field"""
        return parseString(xml_string)

    def _read_exposure_from_dom(self, dom):
        """Reads th exposure time of the experiment into the exposure_time field"""
        if len(dom.getElementsByTagName('Experiment')) != 1:  # check if it is a real v3.0 file
            if len(dom.getElementsByTagName('ShutterTiming')) == 1:  # check if it is a pixis detector
                exposure_time = dom.getElementsByTagName('ExposureTime')[0].childNodes[0]
                return np.float64(exposure_time.toxml()) / 1000.0
            else:
                exposure_time = dom.getElementsByTagName('ReadoutControl')[0]. \
                    getElementsByTagName('Time')[0].childNodes[0].nodeValue
                self.header['accumulations'] = dom.getElementsByTagName('Accumulations')[0].childNodes[0].nodeValue
                return np.float64(exposure_time) * np.float64(self.header['accumulations'])
        else:  # this is searching for legacy experiment:
            self._exposure_time = dom.getElementsByTagName('LegacyExperiment')[0]. \
                getElementsByTagName('Experiment')[0]. \
                getElementsByTagName('CollectionParameters')[0]. \
                getElementsByTagName('Exposure')[0].attributes["value"].value
            return np.float64(self._exposure_time.split()[0])

    def _read_detector_from_dom(self, dom):
        """Reads the detector information from the dom object"""
        self._camera = dom.getElementsByTagName('Camera')
        if len(self._camera) >= 1:
            return self._camera[0].getAttribute('model')
        else:
            return 'unspecified'

    def _read_grating_from_dom(self, dom, infile):
        """Reads the type of grating from the dom Model"""
        try:
            grating = dom.getElementsByTagName('Devices')[0]. \
                getElementsByTagName('Spectrometer')[0]. \
                getElementsByTagName('Grating')[0]. \
                getElementsByTagName('Selected')[0].childNodes[0].toxml()
            return grating.split('[')[1].split(']')[0].replace(',', ' ')
        except IndexError:
            # try from header:
            return str(self._read_at(infile, 650, 1, np.float32)[0])

    def _read_center_wavelength_from_dom(self, dom, infile):
        """Reads the center wavelength from the dom Model and saves it center_wavelength field"""
        try:
            center_wavelength = dom.getElementsByTagName('Devices')[0]. \
                getElementsByTagName('Spectrometer')[0]. \
                getElementsByTagName('Grating')[0]. \
                getElementsByTagName('CenterWavelength')[0]. \
                childNodes[0].toxml()
            return float(center_wavelength)
        except IndexError:
            # try from header
            return float(self._read_at(infile, 72, 1, np.float32)[0])

    def _read_roi_from_dom(self, dom):
        """Reads the ROIs information defined in the SPE file.
        Depending on the modus it will read out:
        For CustomRegions
        roi_x, roi_y, roi_width, roi_height, roi_x_binning, roi_y_binning
        For FullSensor
        roi_x,roi_y, roi_width, roi_height"""
        try:
            roi_modus = str(dom.getElementsByTagName('ReadoutControl')[0].
                            getElementsByTagName('RegionsOfInterest')[0].
                            getElementsByTagName('Selection')[0].
                            childNodes[0].toxml())
            if roi_modus == 'CustomRegions':
                roi_dom = dom.getElementsByTagName('ReadoutControl')[0]. \
                    getElementsByTagName('RegionsOfInterest')[0]. \
                    getElementsByTagName('CustomRegions')[0]. \
                    getElementsByTagName('RegionOfInterest')[0]
                roi_x = int(roi_dom.attributes['x'].value)
                roi_y = int(roi_dom.attributes['y'].value)
                roi_width = int(roi_dom.attributes['width'].value)
                roi_height = int(roi_dom.attributes['height'].value)
            else:
                roi_x = 0
                roi_y = 0
                roi_width = self.header['x_dim']
                roi_height = self.header['y_dim']

        except IndexError:
            roi_x = 0
            roi_y = 0
            roi_width = self.header['x_dim']
            roi_height = self.header['y_dim']

        return roi_x, roi_x + roi_width, roi_y, roi_y + roi_height

    def _read_at(self, infile, pos, size, ntype):
        infile.seek(pos)
        dtype = np.dtype(ntype)
        bp = dtype.itemsize
        data = infile.read(size * bp)
        return np.frombuffer(data, dtype)

    def _read_data(self, infile, frame=None):
        if frame is None:
            frame = 0
        dtype = self.DATA_TYPES.get(self.header['data_type'])
        if dtype is None:
            raise RuntimeError("Unsuported data type: %s" % self.header['data_type'])
        number_size = np.dtype(dtype).itemsize
        frame_size = self.header['x_dim'] * self.header['y_dim'] * number_size
        return self._read_frame(infile, 4100 + frame * frame_size)

    def _read_frame(self, infile, pos=None):
        """Reads in a frame at a specific binary position. The following header parameters have to
        be predefined before calling this function:
        datatype - either 0,1,2,3 for float32, int32, int16 or uint16
        x_dim, y_dim - being the dimensions.
        """
        if pos is None:
            pos = infile.tell()
        dtype = self.DATA_TYPES.get(self.header['data_type'])

        if dtype is None:
            return None

        data = self._read_at(infile, pos, self.header['x_dim'] * self.header['y_dim'], dtype)
        return data.reshape((self.header['y_dim'], self.header['x_dim']))


# this is for compatibility with old code:
speimage = SpeImage
