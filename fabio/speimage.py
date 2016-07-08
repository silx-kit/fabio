# coding: utf-8
#
#    Project: X-ray image reader
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


"""Template for FabIO image reader

This is a template for adding new file formats to FabIO

We hope it will be relatively easy to add new file formats to fabio in the future. 
The basic idea is the following:

1) inherit from FabioImage overriding the methods _readheader, read and optionally write.
   Name your new module XXXimage where XXX means something (eg tifimage).

2) readheader fills in a dictionary of "name":"value" pairs in self.header.
   No one expects to find anything much in there.

3) read fills in self.data with a numpy array holding the image.
   Some info are automatically exposed from data: 
   * self.dim1 and self.dim2: the image dimensions,
   * self.bpp is the bytes per pixel 
   * self.bytecode is the numpy.dtype.type of the data.

4) The member variables "_need_a_seek_to_read" and "_need_a_real_file" are there 
   in case you have
   trouble with the transparent handling of bz2 and gz files.

5) Register the file type (extension naming) in fabioutils.FILETYPES
   TODO: place this in the class definition soon

6) Add your new module as an import into fabio.openimage. 
   Your class will be registered automatically.

7) Fill out the magic numbers for your format in fabio.openimage if you know them
   (the characteristic first few bytes in the file)

8) Upload a testimage to the file release system and create a unittest testcase
   which opens an example of your new format, confirming the image has actually
   been read in successfully (eg check the mean, max, min and esd are all correct,
   perhaps orientation too)

9) Run pylint on your code and then please go clean it up. Have a go at mine 
   while you are at it, before requesting a pull-request on github.

10) Bask in the warm glow of appreciation when someone unexpectedly learns they 
   don't need to convert their data into another format

"""
# Get ready for python3:
from __future__ import with_statement, print_function, division

__authors__ = ["Clemens Prescher"]
__contact__ = "c.prescher@uni-koeln.de"
__license__ = "MIT"
__copyright__ = "Clemens Prescher"
__date__ = "07/07/2016"

import logging

logger = logging.getLogger("speimage")

import datetime
from xml.dom.minidom import parseString

import numpy as np
from numpy.polynomial.polynomial import polyval

from .fabioimage import FabioImage


class SpeImage(FabioImage):
    """FabIO image class for Images for XXX detector
    
    Put some documentation here
    """

    def __init__(self, *arg, **kwargs):
        """
        Generic constructor
        """
        FabioImage.__init__(self, *arg, **kwargs)

    def _readheader(self, infile):
        """
        Read and decode the header of an image:
        
        @param infile: Opened python file (can be stringIO or bipped file)  
        """

        self.header['version'] = self._get_version(infile)

        self.header['data_type'] = self._read_at(108, 1, np.uint16)[0]
        self.header['x_dim'] = np.int64(self._read_at(42, 1, np.int16)[0])
        self.header['y_dim'] = np.int64(self._read_at(656, 1, np.int16)[0])
        self.header['num_frames'] = self._read_at(1446, 1, np.int32)[0]

        if self.header['version'] == 2:
            self.header['time'] = self._read_date_time_from_header()
            self.header['x_calibration'] = self._read_calibration_from_header()
            self.header['exposure_time'] = self._read_at(10, 1, np.float32)[0]
            self.header['detector'] = 'unspecified'
            self.header['grating'] = str(self._read_at(650, 1, np.float32)[0])
            self.header['center_wavelength'] = float(self._read_at(72, 1, np.float32)[0])
            # # self._read_roi_from_header()
            # self._read_num_frames_from_header()
            # self._read_num_combined_frames_from_header()
        elif self.header['version'] == 3:
            self._get_xml_string()
            self._create_dom_from_xml()
            self.header['time'] = self._read_date_time_from_dom()
            self.header['roi'] = self._read_roi_from_dom()
            self.header['x_calibration'] = self._read_calibration_from_dom()
            self.header['exposure_time'] = self._read_exposure_from_dom()
            self.header['detector'] = self._read_detector_from_dom()
            self.header['grating'] = self._read_grating_from_dom()
            self.header['center_wavelength'] = self._read_center_wavelength_from_dom()

        self.header = self.check_header(self.header)

    def read(self, fname, frame=None):
        """
        try to read image 
        @param fname: name of the file
        @param frame: 
        """

        self.resetvals()

        self._infile = open(fname, 'rb')
        self._readheader(self._infile)

        # read the image data and declare
        self.data = self._read_data(frame)

        return self

    def _get_version(self, infile):
        self.xml_offset = self._read_at(678, 1, np.long)
        if self.xml_offset == [0]:
            return 2
        else:
            return 3

    def _read_date_time_from_header(self):
        """Reads the collection time from the header into the date_time field"""
        raw_date = self._read_at(20, 9, np.int8)
        raw_time = self._read_at(172, 6, np.int8)
        str_date = ''.join([chr(i) for i in raw_date])
        str_date += ''.join([chr(i) for i in raw_time])
        date_time = datetime.datetime.strptime(str_date, "%d%b%Y%H%M%S")
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
        return self._read_frame(4100 + frame * frame_size)

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
        else:
            return None
        return data.reshape((self.header['y_dim'], self.header['x_dim']))

    def get_file_size(self):
        self._infile.seek(0, 2)
        self.file_size = self._infile.tell()
        return self.file_size


# this is not compatibility with old code:
speimage = SpeImage