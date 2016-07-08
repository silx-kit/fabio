"""Implements the SPE_File class for loading princeton instrument binary SPE files into Python
works for version 2 and version 3 files.

Usage:
mydata = SPE_File('data.spe')

most important properties:

num_frames - number of frames collected
exposure_time

img - 2d data if num_frames==1
      list of 2d data if num_frames>1  

x_calibration - wavelength information of x-axis



the data will be automatically loaded and all important parameters and the data 
can be requested from the object.
"""

import datetime
from xml.dom.minidom import parseString

import numpy as np
from numpy.polynomial.polynomial import polyval


class SpeImage(object):
    def __init__(self):
        """
        """
        super(SpeImage, self).__init__()
        self.header = {}


    def _read_header(self, infile):
        """
        Read and decode the header of an image:

        @param infile: Opened python file (can be stringIO or bipped file)
        """
        self.header['version'] = self._get_version(infile)

        self.header['data_type'] = self._read_at(108, 1, np.uint16)[0]
        self.header['x_dim'] = np.int64(self._read_at(42, 1, np.int16)[0])
        self.header['y_dim'] = np.int64(self._read_at(656, 1, np.int16)[0])
        self.header['num_frames'] = self._read_at(1446, 1, np.int32)[0]

        if self.header['version']==2:
            self.header['time'] = self._read_date_time_from_header()
            self.header['x_calibration'] = self._read_calibration_from_header()
            self.header['exposure_time'] = self._read_at(10, 1, np.float32)[0]
            self.header['detector'] = 'unspecified'
            self.header['grating'] = str(self._read_at(650, 1, np.float32)[0])
            self.header['center_wavelength'] = float(self._read_at(72, 1, np.float32)[0])
            # # self._read_roi_from_header()
            # self._read_num_frames_from_header()
            # self._read_num_combined_frames_from_header()
        elif self.header['version']==3:
            self._get_xml_string()
            self._create_dom_from_xml()
            self.header['time'] = self._read_date_time_from_dom()
            self.header['roi'] = self._read_roi_from_dom()
            self.header['x_calibration'] = self._read_calibration_from_dom()
            self.header['exposure_time'] = self._read_exposure_from_dom()
            self.header['detector'] = self._read_detector_from_dom()
            self.header['grating'] = self._read_grating_from_dom()
            self.header['center_wavelength'] = self._read_center_wavelength_from_dom()

    def read(self, fname, frame=None):
        self.filename = fname
        self._infile = open(fname, 'rb')
        self._read_header(self._infile)

        self.data = self._read_data(frame)
        self._infile.close()

    def _get_version(self, infile):
        self.xml_offset = self._read_at(678, 1, np.long)
        if self.xml_offset == [0]:
            return 2
        else:
            return 3

    def _read_date_time_from_header(self):
        """Reads the collection time from the header into the date_time field"""
        rawdate = self._read_at(20, 9, np.int8)
        rawtime = self._read_at(172, 6, np.int8)
        strdate = ''.join([chr(i) for i in rawdate])
        strdate += ''.join([chr(i) for i in rawtime])
        date_time = datetime.datetime.strptime(strdate, "%d%b%Y%H%M%S")
        return date_time.strftime("%m/%d/%Y %H:%M:%S")

    def _read_date_time_from_dom(self):
        """Reads the time of collection and saves it date_time field"""
        date_time_str = self.dom.getElementsByTagName('Origin')[0].getAttribute('created')
        try:
            date_time = datetime.datetime.strptime(date_time_str[:-7], "%Y-%m-%dT%H:%M:%S.%f")
            return date_time.strftime("%m/%d/%Y %H:%M:%S.%f")
        except ValueError:
            date_time = datetime.datetime.strptime(date_time_str[:-6], "%Y-%m-%dT%H:%M:%S")
            return date_time.strftime("%m/%d/%Y %H:%M:%S")

    def _read_calibration_from_header(self):
        """Reads the calibration from the header into the x_calibration field"""
        x_polynocoeff = self._read_at(3263, 6, np.double)
        x_val = np.arange(self.header['x_dim']) + 1
        return np.array(polyval(x_val, x_polynocoeff))

    def _read_calibration_from_dom(self):
        """Reads the x calibration of the image from the xml footer and saves
        it in the x_calibration field"""
        spe_format = self.dom.childNodes[0]
        calibrations = spe_format.getElementsByTagName('Calibrations')[0]
        wavelengthmapping = calibrations.getElementsByTagName('WavelengthMapping')[0]
        wavelengths = wavelengthmapping.getElementsByTagName('Wavelength')[0]
        wavelength_values = wavelengths.childNodes[0]
        x_calibration = np.array([float(i) for i in wavelength_values.toxml().split(',')])
        return x_calibration[self.header['roi'][0]:self.header['roi'][1]]

    def _read_num_frames_from_header(self):
        self.num_frames = self._read_at(1446, 1, np.int32)[0]

    def _get_xml_string(self):
        """Reads out the xml string from the file end"""
        xml_size = self.get_file_size() - self.xml_offset
        xml = self._read_at(self.xml_offset, xml_size, np.byte)
        self.xml_string = ''.join([chr(i) for i in xml])
        # if self.debug:
        #     fid = open(self.filename + '.xml', 'w')
        #     for line in self.xml_string:
        #         fid.write(line)
        #     fid.close()

    def _create_dom_from_xml(self):
        """Creates a DOM representation of the xml footer and saves it in the
        dom field"""
        self.dom = parseString(self.xml_string)

    def _read_exposure_from_dom(self):
        """Reads th exposure time of the experiment into the exposure_time field"""
        if len(self.dom.getElementsByTagName('Experiment')) != 1:  # check if it is a real v3.0 file
            if len(self.dom.getElementsByTagName('ShutterTiming')) == 1:  # check if it is a pixis detector
                exposure_time = self.dom.getElementsByTagName('ExposureTime')[0].childNodes[0]
                return np.float(exposure_time.toxml()) / 1000.0
            else:
                exposure_time = self.dom.getElementsByTagName('ReadoutControl')[0]. \
                    getElementsByTagName('Time')[0].childNodes[0].nodeValue
                self.header['accumulations'] = self.dom.getElementsByTagName('Accumulations')[0].childNodes[0].nodeValue
                return np.float(exposure_time) * np.float(self.header['accumulations'])
        else:  # this is searching for legacy experiment:
            self._exposure_time = self.dom.getElementsByTagName('LegacyExperiment')[0]. \
                getElementsByTagName('Experiment')[0]. \
                getElementsByTagName('CollectionParameters')[0]. \
                getElementsByTagName('Exposure')[0].attributes["value"].value
            return np.float(self._exposure_time.split()[0])

    def _read_detector_from_dom(self):
        """Reads the detector information from the dom object"""
        self._camera = self.dom.getElementsByTagName('Camera')
        if len(self._camera) >= 1:
            return self._camera[0].getAttribute('model')
        else:
            return 'unspecified'

    def _read_grating_from_dom(self):
        """Reads the type of grating from the dom Model"""
        try:
            grating = self.dom.getElementsByTagName('Devices')[0]. \
                getElementsByTagName('Spectrometer')[0]. \
                getElementsByTagName('Grating')[0]. \
                getElementsByTagName('Selected')[0].childNodes[0].toxml()
            return grating.split('[')[1].split(']')[0].replace(',', ' ')
        except IndexError:
            # try from header:
            return str(self._read_at(650, 1, np.float32)[0])

    def _read_center_wavelength_from_dom(self):
        """Reads the center wavelength from the dom Model and saves it center_wavelength field"""
        try:
            center_wavelength = self.dom.getElementsByTagName('Devices')[0]. \
                getElementsByTagName('Spectrometer')[0]. \
                getElementsByTagName('Grating')[0]. \
                getElementsByTagName('CenterWavelength')[0]. \
                childNodes[0].toxml()
            return float(center_wavelength)
        except IndexError:
            # try from header
            return float(self._read_at(72, 1, np.float32)[0])

    def _read_roi_from_dom(self):
        """Reads the ROIs information defined in the SPE file.
        Depending on the modus it will read out:
        For CustomRegions
        roi_x, roi_y, roi_width, roi_height, roi_x_binning, roi_y_binning
        For FullSensor
        roi_x,roi_y, roi_width, roi_height"""
        try:
            roi_modus = str(self.dom.getElementsByTagName('ReadoutControl')[0]. \
                                 getElementsByTagName('RegionsOfInterest')[0]. \
                                 getElementsByTagName('Selection')[0]. \
                                 childNodes[0].toxml())
            if roi_modus == 'CustomRegions':
                roi_dom = self.dom.getElementsByTagName('ReadoutControl')[0]. \
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

    def _read_at(self, pos, size, ntype):
        self._infile.seek(pos)
        return np.fromfile(self._infile, ntype, size)

    def _read_data(self, frame=None):
        if frame is None:
            frame = 0
        if self.header['data_type'] == 0:
            number_size = np.float32().itemsize
        elif self.header['data_type'] == 1:
            number_size = np.int32().itemsize
        elif self.header['data_type'] == 2:
            number_size = np.int16().itemsize
        elif self.header['data_type'] == 3:
            number_size = np.int32().itemsize
        frame_size = self.header['x_dim'] * self.header['y_dim'] * number_size
        return self._read_frame(4100+frame*frame_size)

    def _read_frame(self, pos=None):
        """Reads in a frame at a specific binary position. The following header parameters have to
        be predefined before calling this function:
        datatype - either 0,1,2,3 for float32, int32, int16 or uint16
        x_dim, y_dim - being the dimensions.
        """
        if pos == None:
            pos = self._infile.tell()
        if self.header['data_type'] == 0:
            data = self._read_at(pos, self.header['x_dim'] * self.header['y_dim'], np.float32)
        elif self.header['data_type'] == 1:
            data = self._read_at(pos, self.header['x_dim'] * self.header['y_dim'], np.int32)
        elif self.header['data_type'] == 2:
            data = self._read_at(pos, self.header['x_dim'] * self.header['y_dim'], np.int16)
        elif self.header['data_type'] == 3:
            data = self._read_at(pos, self.header['x_dim'] * self.header['y_dim'], np.uint16)
        return data.reshape((self.header['y_dim'], self.header['x_dim']))

    def get_file_size(self):
        self._infile.seek(0, 2)
        self.file_size = self._infile.tell()
        return self.file_size
