#!/usr/bin/env python

#
# Reads the header from a GE a-Si Angio Detector
# Using version 8001 of the header from file:
#     c:\adept\core\DefaultImageInfoConfig.csv
#
#  Antonino Miceli
#  Thu Jan  4 13:46:31 CST 2007
#

# modifications by Jon Wright for style, pychecker and fabio
# 

import numpy as np
import struct, logging
from fabioimage import fabioimage
from fabioutils import next_filename, previous_filename

GE_HEADER_INFO = [
    # Name, length in bytes, format for struct (None means string)
    ('ImageFormat', 10, None),
    ('VersionOfStandardHeader', 2, '=H'),
    ('StandardHeaderSizeInBytes', 4, '=L'),
    ('VersionOfUserHeader', 2, '=H'),
    ('UserHeaderSizeInBytes', 4, '=L'),
    ('NumberOfFrames', 2, '=H'),
    ('NumberOfRowsInFrame', 2, '=H'),
    ('NumberOfColsInFrame', 2, '=H'),
    ('ImageDepthInBits', 2, '=H'),
    ('AcquisitionDate', 20, None),
    ('AcquisitionTime', 20, None),
    ('DUTID', 20, None),
    ('Operator', 50, None),
    ('DetectorSignature', 20, None),
    ('TestSystemName', 20, None),
    ('TestStationRevision', 20, None),
    ('CoreBundleRevision', 20, None),
    ('AcquisitionName', 40, None),
    ('AcquisitionParameterRevision', 20, None),
    ('OriginalNumberOfRows', 2, '=H'),
    ('OriginalNumberOfColumns', 2, '=H'),
    ('RowNumberUpperLeftPointArchiveROI', 2, '=H'),
    ('ColNumberUpperLeftPointArchiveROI', 2, '=H'),
    ('Swapped', 2, '=H'),
    ('Reordered', 2, '=H'),
    ('HorizontalFlipped', 2, '=H'),
    ('VerticalFlipped', 2, '=H'),
    ('WindowValueDesired', 2, '=H'),
    ('LevelValueDesired', 2, '=H'),
    ('AcquisitionMode', 2, '=H'),
    ('AcquisitionType', 2, '=H'),
    ('UserAcquisitionCoffFileName1', 100, None),
    ('UserAcquisitionCoffFileName2', 100, None),
    ('FramesBeforeExpose', 2, '=H'),
    ('FramesDuringExpose', 2, '=H'),
    ('FramesAfterExpose', 2, '=H'),
    ('IntervalBetweenFrames', 2, '=H'),
    ('ExposeTimeDelayInMicrosecs', 8, '=d'),
    ('TimeBetweenFramesInMicrosecs', 8, '=d'),
    ('FramesToSkipExpose', 2, '=H'),
    ('ExposureMode', 2, '=H'),
    ('PrepPresetTimeInMicrosecs', 8, '=d'),
    ('ExposePresetTimeInMicrosecs', 8, '=d'),
    ('AcquisitionFrameRateInFps', 4, '=f'),
    ('FOVSelect', 2, '=H'),
    ('ExpertMode', 2, '=H'),
    ('SetVCommon1', 8, '=d'),
    ('SetVCommon2', 8, '=d'),
    ('SetAREF', 8, '=d'),
    ('SetAREFTrim', 4, '=L'),
    ('SetSpareVoltageSource', 8, '=d'),
    ('SetCompensationVoltageSource', 8, '=d'),
    ('SetRowOffVoltage', 8, '=d'),
    ('SetRowOnVoltage', 8, '=d'),
    ('StoreCompensationVoltage', 4, '=L'),
    ('RampSelection', 2, '=H'),
    ('TimingMode', 2, '=H'),
    ('Bandwidth', 2, '=H'),
    ('ARCIntegrator', 2, '=H'),
    ('ARCPostIntegrator', 2, '=H'),
    ('NumberOfRows', 4, '=L'),
    ('RowEnable', 2, '=H'),
    ('EnableStretch', 2, '=H'),
    ('CompEnable', 2, '=H'),
    ('CompStretch', 2, '=H'),
    ('LeftEvenTristate', 2, '=H'),
    ('RightOddTristate', 2, '=H'),
    ('TestModeSelect', 4, '=L'),
    ('AnalogTestSource', 4, '=L'),
    ('VCommonSelect', 4, '=L'),
    ('DRCColumnSum', 4, '=L'),
    ('TestPatternFrameDelta', 4, '=L'),
    ('TestPatternRowDelta', 4, '=L'),
    ('TestPatternColumnDelta', 4, '=L'),
    ('DetectorHorizontalFlip', 2, '=H'),
    ('DetectorVerticalFlip', 2, '=H'),
    ('DFNAutoScrubOnOff', 2, '=H'),
    ('FiberChannelTimeOutInMicrosecs', 4, '=L'),
    ('DFNAutoScrubDelayInMicrosecs', 4, '=L'),
    ('StoreAECROI', 2, '=H'),
    ('TestPatternSaturationValue', 2, '=H'),
    ('TestPatternSeed', 4, '=L'),
    ('ExposureTimeInMillisecs', 4, '=f'),
    ('FrameRateInFps', 4, '=f'),
    ('kVp', 4, '=f'),
    ('mA', 4, '=f'),
    ('mAs', 4, '=f'),
    ('FocalSpotInMM', 4, '=f'),
    ('GeneratorType', 20, None),
    ('StrobeIntensityInFtL', 4, '=f'),
    ('NDFilterSelection', 2, '=H'),
    ('RefRegTemp1', 8, '=d'),
    ('RefRegTemp2', 8, '=d'),
    ('RefRegTemp3', 8, '=d'),
    ('Humidity1', 4, '=f'),
    ('Humidity2', 4, '=f'),
    ('DetectorControlTemp', 8, '=d'),
    ('DoseValueInmR', 8, '=d'),
    ('TargetLevelROIRow0', 2, '=H'),
    ('TargetLevelROICol0', 2, '=H'),
    ('TargetLevelROIRow1', 2, '=H'),
    ('TargetLevelROICol1', 2, '=H'),
    ('FrameNumberForTargetLevelROI', 2, '=H'),
    ('PercentRangeForTargetLevel', 2, '=H'),
    ('TargetValue', 2, '=H'),
    ('ComputedMedianValue', 2, '=H'),
    ('LoadZero', 2, '=H'),
    ('MaxLUTOut', 2, '=H'),
    ('MinLUTOut', 2, '=H'),
    ('MaxLinear', 2, '=H'),
    ('Reserved', 2, '=H'),
    ('ElectronsPerCount', 2, '=H'),
    ('ModeGain', 2, '=H'),
    ('TemperatureInDegC', 8, '=d'),
    ('LineRepaired', 2, '=H'),
    ('LineRepairFileName', 100, None),
    ('CurrentLongitudinalInMM', 4, '=f'),
    ('CurrentTransverseInMM', 4, '=f'),
    ('CurrentCircularInMM', 4, '=f'),
    ('CurrentFilterSelection', 4, '=L'),
    ('DisableScrubAck', 2, '=H'),
    ('ScanModeSelect', 2, '=H'),
    ('DetectorAppSwVersion', 20, None),
    ('DetectorNIOSVersion', 20, None),
    ('DetectorPeripheralSetVersion', 20, None),
    ('DetectorPhysicalAddress', 20, None),
    ('PowerDown', 2, '=H'),
    ('InitialVoltageLevel_VCOMMON', 8, '=d'),
    ('FinalVoltageLevel_VCOMMON', 8, '=d'),
    ('DmrCollimatorSpotSize', 10, None),
    ('DmrTrack', 5, None),
    ('DmrFilter', 5, None),
    ('FilterCarousel', 2, '=H'),
    ('Phantom', 20, None),
    ('SetEnableHighTime', 2, '=H'),
    ('SetEnableLowTime', 2, '=H'),
    ('SetCompHighTime', 2, '=H'),
    ('SetCompLowTime', 2, '=H'),
    ('SetSyncLowTime', 2, '=H'),
    ('SetConvertLowTime', 2, '=H'),
    ('SetSyncHighTime', 2, '=H'),
    ('SetEOLTime', 2, '=H'),
    ('SetRampOffsetTime', 2, '=H'),
    ('FOVStartingValue', 2, '=H'),
    ('ColumnBinning', 2, '=H'),
    ('RowBinning', 2, '=H'),
    ('BorderColumns64', 2, '=H'),
    ('BorderRows64', 2, '=H'),
    ('FETOffRows64', 2, '=H'),
    ('FOVStartColumn128', 2, '=H'),
    ('FOVStartRow128', 2, '=H'),
    ('NumberOfColumns128', 2, '=H'),
    ('NumberOfRows128', 2, '=H'),
    ('VFPAquisition', 2000, None),
    ('Comment', 200, None)
    ]


class GEimage(fabioimage):

    _need_a_seek_to_read = True

    def _readheader(self, infile):
        """ Read a GE image header """

        infile.seek(0)

        self.header = {}
        for name, nbytes, format in GE_HEADER_INFO:
            if format is None:
                self.header[ name ] = infile.read(nbytes)
            else:
                self.header[ name ] = struct.unpack(format,
                                                     infile.read(nbytes))[0]

    def read(self, fname, frame=0):
        """
        Read in header into self.header and
        the data   into self.data
        """
        self.header = {}
        self.resetvals()
        infile = self._open(fname, "rb")
        self.sequencefilename = fname
        self._readheader(infile)
        self.nframes = self.header['NumberOfFrames']
        self._readframe(infile, frame)
        infile.close()
        return self

    def _makeframename(self):
        """ The thing to be printed for the user to represent a frame inside
        a file """
        self.filename = "%s$%04d" % (self.sequencefilename,
                                   self.currentframe)

    def _readframe(self, filepointer, img_num):
        """
        # Load only one image from the sequence
        #    Note: the first image in the sequence 0
        # raises an exception if you give an invalid image
        # otherwise fills in self.data
        """
        if(img_num > self.nframes or img_num < 0):
            raise Exception("Bad image number")
        imgstart = self.header['StandardHeaderSizeInBytes'] + \
                   self.header['UserHeaderSizeInBytes'] + \
                   img_num * self.header['NumberOfRowsInFrame'] * \
                   self.header['NumberOfColsInFrame'] * \
                   self.header['ImageDepthInBits'] / 8
        # whence = 0 means seek from start of file
        filepointer.seek(imgstart, 0)

        self.bpp = self.header['ImageDepthInBits'] / 8 # hopefully 2        
        imglength = self.header['NumberOfRowsInFrame'] * \
                    self.header['NumberOfColsInFrame'] * self.bpp
        if self.bpp != 2:
            logging.warning("Using uint16 for GE but seems to be wrong")

        # Guessing it is always unsigned int?
        self.data = np.fromstring(filepointer.read(imglength), np.uint16)
        self.data.shape = (self.header['NumberOfRowsInFrame'],
                            self.header['NumberOfColsInFrame'])
        self.dim2 , self.dim1 = self.data.shape
        self.currentframe = int(img_num)
        self._makeframename()


    def write(self, fname, force_type=np.uint16):
        """ Not yet implemented"""
        raise Exception("Write is not implemented")

    def getframe(self, num):
        """
        Returns a frame as a new fabioimage object
        """
        if num < 0 or num > self.nframes:
            raise Exception("Requested frame number is out of range")
        # Do a deep copy of the header to make a new one
        newheader = {}
        for k in self.header.keys():
            newheader[k] = self.header[k]
        frame = GEimage(header=newheader)
        frame.nframes = self.nframes
        frame.sequencefilename = self.sequencefilename
        infile = frame._open(self.sequencefilename, "rb")
        frame._readframe(infile, num)
        infile.close()
        return frame

    def next(self):
        """
        Get the next image in a series as a fabio image
        """
        if self.currentframe < (self.nframes - 1) and self.nframes > 1:
            return self.getframe(self.currentframe + 1)
        else:
            newobj = GEimage()
            newobj.read(next_filename(
                self.sequencefilename))
            return newobj

    def previous(self):
        """
        Get the previous image in a series as a fabio image
        """
        if self.currentframe > 0:
            return self.getframe(self.currentframe - 1)
        else:
            newobj = GEimage()
            newobj.read(previous_filename(
                self.sequencefilename))
            return newobj


def demo():
    import sys, time

    if len(sys.argv) < 2:
        print "USAGE: GE_script.py <GEaSi_raw_image_file>"
        sys.exit()

    image_file = sys.argv[1]

    print "init read_GEaSi_data class and load header.."
    sequence1 = GEimage()
    sequence1.read(image_file)

    print "TimeBetweenFramesInMicrosecs = ",
    print sequence1.header['TimeBetweenFramesInMicrosecs']
    print "AcquisitionTime = ",
    print sequence1.header['AcquisitionTime']


    print "Mean = ", sequence1.data.ravel().mean()

    while 1:
        start = time.time()
        try:
            sequence1 = sequence1.next()
            print sequence1.currentframe, sequence1.data.ravel().mean(), \
                  time.time() - start
        except:
            raise
            break




if __name__ == '__main__':
    demo()
