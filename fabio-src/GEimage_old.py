
#!/usr/bin/env python

"""
Reads the header from a GE a-Si Angio Detector

Authors: Henning O. Sorensen & Erik Knudsen
         Center for Fundamental Research: Metal Structures in Four Dimensions
         Risoe National Laboratory
         Frederiksborgvej 399
         DK-4000 Roskilde
         email:erik.knudsen@risoe.dk

        + Jon Wright, ESRF

        The header information has been taken from the script read_GEaSi_data.py
        by
        Antonino Miceli
        Thu Jan  4 13:46:31 CST 2007

"""

import numpy
from fabioimage import fabioimage

class GEimage(fabioimage):


    def _readheader(self, infile):

        infile.seek(0)

        # ADEPT
        self.ImageFormat = infile.read(10)

        # USHORT --> "=H"
        # ULONG  --> "=L"
        #   = means byte order is native

        self.header['HeaderVersion'] = numpy.fromstring(infile.read(2), numpy.uint16)[0]
        self.header['HeaderSizeInBytes'] = int(numpy.fromstring(infile.read(4), numpy.uint32)[0])
        self.header['UserHeaderVersion'] = numpy.fromstring(infile.read(2), numpy.uint16)[0]
        self.header['UserHeaderSizeInBytes'] = int(numpy.fromstring(infile.read(4), numpy.uint32)[0])

        self.header['NumberOfFrames'] = numpy.fromstring(infile.read(2), numpy.uint16)[0]
        self.header['NumberOfRowsInFrame'] = numpy.fromstring(infile.read(2), numpy.uint16)[0]
        self.header['NumberOfColsInFrame'] = numpy.fromstring(infile.read(2), numpy.uint16)[0]
        self.header['BitsPerPixel'] = numpy.fromstring(infile.read(2), numpy.uint16)[0]

        self.header['AcquisitionDate'] = infile.read(20)
        self.header['AcquisitionTime'] = infile.read(20)

        self.DUTID = infile.read(20)

        self.header['Operator'] = infile.read(50)

        self.header['DetectorSignature'] = infile.read(20)
        self.header['TestSystemName'] = infile.read(20)
        self.header['TestStationRevision'] = infile.read(20)
        self.header['CoreBundleRevision'] = infile.read(20)
        self.header['AcquisitionName'] = infile.read(40)
        self.header['AcquisitionParameterRevision'] = infile.read(20)

#         self.OriginalNumberOfRows = infile.read(2)
#         self.OriginalNumberOfRows = struct.unpack("=H",self.OriginalNumberOfRows)[0]

#         self.OriginalNumberOfColumns = infile.read(2)
#         self.OriginalNumberOfColumns = struct.unpack("=H",self.OriginalNumberOfColumns)[0]

#         self.RowNumberUpperLeftPointArchiveROI = infile.read(2)
#         self.RowNumberUpperLeftPointArchiveROI = struct.unpack("=H",self.RowNumberUpperLeftPointArchiveROI)[0]

#         self.ColNumberUpperLeftPointArchiveROI = infile.read(2)
#         self.ColNumberUpperLeftPointArchiveROI = struct.unpack("=H",self.ColNumberUpperLeftPointArchiveROI)[0]

#         self.Swapped = infile.read(2) 
#         self.Swapped = struct.unpack("=H",self.Swapped)[0]

#         self.Reordered = infile.read(2) 
#         self.Reordered = struct.unpack("=H",self.Reordered)[0]

#         self.HorizontalFlipped = infile.read(2) 
#         self.HorizontalFlipped = struct.unpack("=H",self.HorizontalFlipped)[0]

#         self.VerticalFlipped = infile.read(2) 
#         self.VerticalFlipped = struct.unpack("=H",self.VerticalFlipped)[0]

#         self.WindowValueDesired = infile.read(2) 
#         self.WindowValueDesired = struct.unpack("=H",self.WindowValueDesired)[0]

#         self.LevelValueDesired = infile.read(2) 
#         self.LevelValueDesired = struct.unpack("=H",self.LevelValueDesired)[0]

#         self.AcquisitionMode = infile.read(2) 
#         self.AcquisitionMode = struct.unpack("=H",self.AcquisitionMode)[0]

#         self.AcquisitionType = infile.read(2) 
#         self.AcquisitionType = struct.unpack("=H",self.AcquisitionType)[0]

#         self.UserAcquisitionCoffFileName1 = infile.read(100) 
#         self.UserAcquisitionCoffFileName2 = infile.read(100) 

#         self.FramesBeforeExpose = infile.read(2) 
#         self.FramesBeforeExpose = struct.unpack("=H",self.FramesBeforeExpose)[0]

#         self.FramesDuringExpose = infile.read(2)  
#         self.FramesDuringExpose = struct.unpack("=H",self.FramesDuringExpose)[0]

#         self.FramesAfterExpose = infile.read(2) 
#         self.FramesAfterExpose = struct.unpack("=H",self.FramesAfterExpose)[0]

#         self.IntervalBetweenFrames = infile.read(2) 
#         self.IntervalBetweenFrames = struct.unpack("=H",self.IntervalBetweenFrames)[0]

#         self.ExposeTimeDelayInMicrosecs = infile.read(8) 
#         self.ExposeTimeDelayInMicrosecs = struct.unpack("=d",self.ExposeTimeDelayInMicrosecs)[0]

#         self.TimeBetweenFramesInMicrosecs = infile.read(8) 
#         self.TimeBetweenFramesInMicrosecs = struct.unpack("=d",self.TimeBetweenFramesInMicrosecs)[0]

#         self.FramesToSkipExpose = infile.read(2) 
#         self.FramesToSkipExpose = struct.unpack("=H",self.FramesToSkipExpose)[0]

#         # Rad --> ExposureMode = 1
#         self.ExposureMode = infile.read(2) 
#         self.ExposureMode = struct.unpack("=H",self.ExposureMode)[0]

#         self.PrepPresetTimeInMicrosecs = infile.read(8) 
#         self.PrepPresetTimeInMicrosecs = struct.unpack("=d",self.PrepPresetTimeInMicrosecs)[0]

#         self.ExposePresetTimeInMicrosecs = infile.read(8) 
#         self.ExposePresetTimeInMicrosecs = struct.unpack("=d",self.ExposePresetTimeInMicrosecs)[0]

#         self.AcquisitionFrameRateInFps = infile.read(4) 
#         self.AcquisitionFrameRateInFps = struct.unpack("=f",self.AcquisitionFrameRateInFps)[0]

#         self.FOVSelect = infile.read(2)
#         self.FOVSelect = struct.unpack("=H",self.FOVSelect)[0]

#         self.ExpertMode = infile.read(2)
#         self.ExpertMode = struct.unpack("=H",self.ExpertMode)[0]

#         self.SetVCommon1 = infile.read(8)
#         self.SetVCommon1 = struct.unpack("=d",self.SetVCommon1)[0]

#         self.SetVCommon2 = infile.read(8)
#         self.SetVCommon2 = struct.unpack("=d",self.SetVCommon2)[0]

#         self.SetAREF = infile.read(8)
#         self.SetAREF = struct.unpack("=d",self.SetAREF)[0]

#         self.SetAREFTrim = infile.read(4)
#         self.SetAREFTrim = struct.unpack("=L",self.SetAREFTrim)[0]

#         self.SetSpareVoltageSource = infile.read(8)
#         self.SetSpareVoltageSource = struct.unpack("=d",self.SetSpareVoltageSource)[0]

#         self.SetCompensationVoltageSource = infile.read(8)
#         self.SetCompensationVoltageSource = struct.unpack("=d",self.SetCompensationVoltageSource)[0]

#         self.SetRowOffVoltage = infile.read(8)
#         self.SetRowOffVoltage = struct.unpack("=d",self.SetRowOffVoltage)[0]

#         self.SetRowOnVoltage = infile.read(8)
#         self.SetRowOnVoltage = struct.unpack("=d",self.SetRowOnVoltage)[0]

#         self.StoreCompensationVoltage = infile.read(4)
#         self.StoreCompensationVoltage = struct.unpack("=L",self.StoreCompensationVoltage)[0]

#         self.RampSelection = infile.read(2)
#         self.RampSelection = struct.unpack("=H",self.RampSelection)[0]

#         self.TimingMode = infile.read(2)
#         self.TimingMode = struct.unpack("=H",self.TimingMode)[0]

#         self.Bandwidth = infile.read(2)
#         self.Bandwidth = struct.unpack("=H",self.Bandwidth)[0]

#         self.ARCIntegrator = infile.read(2)
#         self.ARCIntegrator = struct.unpack("=H",self.ARCIntegrator)[0]

#         self.ARCPostIntegrator = infile.read(2)
#         self.ARCPostIntegrator = struct.unpack("=H",self.ARCPostIntegrator)[0]

#         self.NumberOfRows = infile.read(4)
#         self.NumberOfRows = struct.unpack("=L",self.NumberOfRows)[0]

#         self.RowEnable = infile.read(2)
#         self.RowEnable = struct.unpack("=H",self.RowEnable)[0]

#         self.EnableStretch = infile.read(2)
#         self.EnableStretch = struct.unpack("=H",self.EnableStretch)[0]

#         self.CompEnable = infile.read(2)
#         self.CompEnable = struct.unpack("=H",self.CompEnable)[0]

#         self.CompStretch = infile.read(2)
#         self.CompStretch = struct.unpack("=H",self.CompStretch)[0]

#         self.LeftEvenTristate = infile.read(2)
#         self.LeftEvenTristate = struct.unpack("=H",self.LeftEvenTristate)[0]

#         self.RightOddTristate = infile.read(2)
#         self.RightOddTristate = struct.unpack("=H",self.RightOddTristate)[0]

#         self.TestModeSelect = infile.read(4)
#         self.TestModeSelect = struct.unpack("=L",self.TestModeSelect)[0]

#         self.AnalogTestSource = infile.read(4)
#         self.AnalogTestSource = struct.unpack("=L",self.AnalogTestSource)[0]

#         self.VCommonSelect = infile.read(4)
#         self.VCommonSelect = struct.unpack("=L",self.VCommonSelect)[0]

#         self.DRCColumnSum = infile.read(4)
#         self.DRCColumnSum = struct.unpack("=L",self.DRCColumnSum)[0]

#         self.TestPatternFrameDelta = infile.read(4)
#         self.TestPatternFrameDelta = struct.unpack("=L",self.TestPatternFrameDelta)[0]

#         self.TestPatternRowDelta = infile.read(4)
#         self.TestPatternRowDelta = struct.unpack("=L",self.TestPatternRowDelta)[0]

#         self.TestPatternColumnDelta = infile.read(4)
#         self.TestPatternColumnDelta = struct.unpack("=L",self.TestPatternColumnDelta)[0]

#         self.DetectorHorizontalFlip = infile.read(2)
#         self.DetectorHorizontalFlip = struct.unpack("=H",self.DetectorHorizontalFlip)[0]

#         self.DetectorVerticalFlip = infile.read(2)
#         self.DetectorVerticalFlip = struct.unpack("=H",self.DetectorVerticalFlip)[0]

#         self.DFNAutoScrubOnOff = infile.read(2)
#         self.DFNAutoScrubOnOff = struct.unpack("=H",self.DFNAutoScrubOnOff)[0]

#         self.FiberChannelTimeOutInMicrosecs = infile.read(4)
#         self.FiberChannelTimeOutInMicrosecs = struct.unpack("=L",self.FiberChannelTimeOutInMicrosecs)[0]

#         self.DFNAutoScrubDelayInMicrosecs = infile.read(4)
#         self.DFNAutoScrubDelayInMicrosecs = struct.unpack("=L",self.DFNAutoScrubDelayInMicrosecs)[0]

#         self.StoreAECROI = infile.read(2)
#         self.StoreAECROI = struct.unpack("=H",self.StoreAECROI)[0]

#         self.TestPatternSaturationValue = infile.read(2)
#         self.TestPatternSaturationValue = struct.unpack("=H",self.TestPatternSaturationValue)[0]

#         self.TestPatternSeed = infile.read(4)
#         self.TestPatternSeed = struct.unpack("=L",self.TestPatternSeed)[0]

#         self.ExposureTimeInMillisecs = infile.read(4) 
#         self.ExposureTimeInMillisecs = struct.unpack("=f",self.ExposureTimeInMillisecs)[0]

#         self.FrameRateInFps = infile.read(4) 
#         self.FrameRateInFps = struct.unpack("=f",self.FrameRateInFps)[0]

#         self.kVp = infile.read(4) 
#         self.kVp = struct.unpack("=f",self.kVp)[0]

#         self.mA = infile.read(4) 
#         self.mA = struct.unpack("=f",self.mA)[0]

#         self.mAs = infile.read(4) 
#         self.mAs = struct.unpack("=f",self.mAs)[0]

#         self.FocalSpotInMM = infile.read(4) 
#         self.FocalSpotInMM = struct.unpack("=f",self.FocalSpotInMM)[0]

#         self.GeneratorType = infile.read(20)

#         self.StrobeIntensityInFtL = infile.read(4) 
#         self.StrobeIntensityInFtL = struct.unpack("=f",self.StrobeIntensityInFtL)[0]

#         self.NDFilterSelection = infile.read(2) 
#         self.NDFilterSelection = struct.unpack("=H",self.NDFilterSelection)[0]

#         self.RefRegTemp1 = infile.read(8) 
#         self.RefRegTemp1 = struct.unpack("=d",self.RefRegTemp1)[0]

#         self.RefRegTemp2 = infile.read(8) 
#         self.RefRegTemp2 = struct.unpack("=d",self.RefRegTemp2)[0]

#         self.RefRegTemp3 = infile.read(8) 
#         self.RefRegTemp3 = struct.unpack("=d",self.RefRegTemp3)[0]

#         self.Humidity1 = infile.read(4) 
#         self.Humidity1 = struct.unpack("=f",self.Humidity1)[0]

#         self.Humidity2 = infile.read(4) 
#         self.Humidity2 = struct.unpack("=f",self.Humidity2)[0]

#         self.DetectorControlTemp = infile.read(8) 
#         self.DetectorControlTemp = struct.unpack("=d",self.DetectorControlTemp)[0]

#         self.DoseValueInmR = infile.read(8) 
#         self.DoseValueInmR = struct.unpack("=d",self.DoseValueInmR)[0]

#         self.TargetLevelROIRow0 = infile.read(2)
#         self.TargetLevelROIRow0 = struct.unpack("=H",self.TargetLevelROIRow0)[0]

#         self.TargetLevelROICol0 = infile.read(2)
#         self.TargetLevelROICol0 = struct.unpack("=H",self.TargetLevelROICol0)[0]

#         self.TargetLevelROIRow1 = infile.read(2)
#         self.TargetLevelROIRow1 = struct.unpack("=H",self.TargetLevelROIRow1)[0]

#         self.TargetLevelROICol1 = infile.read(2)
#         self.TargetLevelROICol1 = struct.unpack("=H",self.TargetLevelROICol1)[0]

#         self.FrameNumberForTargetLevelROI = infile.read(2)
#         self.FrameNumberForTargetLevelROI = struct.unpack("=H",self.FrameNumberForTargetLevelROI)[0]

#         self.PercentRangeForTargetLevel = infile.read(2)
#         self.PercentRangeForTargetLevel = struct.unpack("=H",self.PercentRangeForTargetLevel)[0]

#         self.TargetValue = infile.read(2)
#         self.TargetValue = struct.unpack("=H",self.TargetValue)[0]

#         self.ComputedMedianValue = infile.read(2)
#         self.ComputedMedianValue = struct.unpack("=H",self.ComputedMedianValue)[0]

#         self.LoadZero = infile.read(2)
#         self.LoadZero = struct.unpack("=H",self.LoadZero)[0]

#         self.MaxLUTOut = infile.read(2)
#         self.MaxLUTOut = struct.unpack("=H",self.MaxLUTOut)[0]

#         self.MinLUTOut = infile.read(2)
#         self.MinLUTOut = struct.unpack("=H",self.MinLUTOut)[0]

#         self.MaxLinear = infile.read(2)
#         self.MaxLinear = struct.unpack("=H",self.MaxLinear)[0]

#         self.Reserved = infile.read(2)
#         self.Reserved = struct.unpack("=H",self.Reserved)[0]

#         self.ElectronsPerCount = infile.read(2)
#         self.ElectronsPerCount = struct.unpack("=H",self.ElectronsPerCount)[0]

#         self.ModeGain = infile.read(2)
#         self.ModeGain = struct.unpack("=H",self.ModeGain)[0]

#         self.TemperatureInDegC = infile.read(8)
#         self.TemperatureInDegC = struct.unpack("=d",self.TemperatureInDegC)[0]

#         self.LineRepaired = infile.read(2)
#         self.LineRepaired = struct.unpack("=H",self.LineRepaired)[0]

#         self.LineRepairFileName = infile.read(100)

#         self.CurrentLongitudinalInMM = infile.read(4)
#         self.CurrentLongitudinalInMM = struct.unpack("=f",self.CurrentLongitudinalInMM)[0]

#         self.CurrentTransverseInMM = infile.read(4)
#         self.CurrentTransverseInMM = struct.unpack("=f",self.CurrentTransverseInMM)[0]

#         self.CurrentCircularInMM = infile.read(4)
#         self.CurrentCircularInMM = struct.unpack("=f",self.CurrentCircularInMM)[0]

#         self.CurrentFilterSelection = infile.read(4)
#         self.CurrentFilterSelection = struct.unpack("=L",self.CurrentFilterSelection)[0]

#         self.DisableScrubAck = infile.read(2)
#         self.DisableScrubAck = struct.unpack("=H",self.DisableScrubAck)[0]

#         self.ScanModeSelect = infile.read(2)
#         self.ScanModeSelect = struct.unpack("=H",self.ScanModeSelect)[0]

#         self.DetectorAppSwVersion = infile.read(20)	

#         self.DetectorNIOSVersion = infile.read(20)	

#         self.DetectorPeripheralSetVersion = infile.read(20)	

#         self.DetectorPhysicalAddress	 = infile.read(20)

#         self.PowerDown = infile.read(2)
#         self.PowerDown = struct.unpack("=H",self.PowerDown)[0]

#         self.InitialVoltageLevel_VCOMMON = infile.read(8)
#         self.InitialVoltageLevel_VCOMMON = struct.unpack("=d",self.InitialVoltageLevel_VCOMMON)[0]

#         self.FinalVoltageLevel_VCOMMON = infile.read(8)
#         self.FinalVoltageLevel_VCOMMON = struct.unpack("=d",self.FinalVoltageLevel_VCOMMON)[0]

#         self.DmrCollimatorSpotSize	 = infile.read(10)

#         self.DmrTrack	 = infile.read(5)

#         self.DmrFilter	 = infile.read(5)

#         self.FilterCarousel = infile.read(2)
#         self.FilterCarousel = struct.unpack("=H",self.FilterCarousel)[0]

#         self.Phantom	 = infile.read(20)

#         self.SetEnableHighTime = infile.read(2)
#         self.SetEnableHighTime = struct.unpack("=H",self.SetEnableHighTime)[0]

#         self.SetEnableLowTime = infile.read(2)
#         self.SetEnableLowTime = struct.unpack("=H",self.SetEnableLowTime)[0]

#         self.SetCompHighTime = infile.read(2)
#         self.SetCompHighTime = struct.unpack("=H",self.SetCompHighTime)[0]

#         self.SetCompLowTime = infile.read(2)
#         self.SetCompLowTime = struct.unpack("=H",self.SetCompLowTime)[0]

#         self.SetSyncLowTime = infile.read(2)
#         self.SetSyncLowTime = struct.unpack("=H",self.SetSyncLowTime)[0]

#         self.SetConvertLowTime = infile.read(2)
#         self.SetConvertLowTime = struct.unpack("=H",self.SetConvertLowTime)[0]

#         self.SetSyncHighTime = infile.read(2)
#         self.SetSyncHighTime = struct.unpack("=H",self.SetSyncHighTime)[0]

#         self.SetEOLTime = infile.read(2)
#         self.SetEOLTime = struct.unpack("=H",self.SetEOLTime)[0]

#         self.SetRampOffsetTime = infile.read(2)
#         self.SetRampOffsetTime = struct.unpack("=H",self.SetRampOffsetTime)[0]

#         self.FOVStartingValue = infile.read(2)
#         self.FOVStartingValue = struct.unpack("=H",self.FOVStartingValue)[0]

#         self.ColumnBinning = infile.read(2)
#         self.ColumnBinning = struct.unpack("=H",self.ColumnBinning)[0]

#         self.RowBinning = infile.read(2)
#         self.RowBinning = struct.unpack("=H",self.RowBinning)[0]

#         self.BorderColumns64 = infile.read(2)
#         self.BorderColumns64 = struct.unpack("=H",self.BorderColumns64)[0]

#         self.BorderRows64 = infile.read(2)
#         self.BorderRows64 = struct.unpack("=H",self.BorderRows64)[0]

#         self.FETOffRows64 = infile.read(2)
#         self.FETOffRows64 = struct.unpack("=H",self.FETOffRows64)[0]

#         self.FOVStartColumn128 = infile.read(2)
#         self.FOVStartColumn128 = struct.unpack("=H",self.FOVStartColumn128)[0]

#         self.FOVStartRow128 = infile.read(2)
#         self.FOVStartRow128 = struct.unpack("=H",self.FOVStartRow128)[0]

#         self.NumberOfColumns128 = infile.read(2)
#         self.NumberOfColumns128 = struct.unpack("=H",self.NumberOfColumns128)[0]

#         self.NumberOfRows128 = infile.read(2)
#         self.NumberOfRows128 = struct.unpack("=H",self.NumberOfRows128)[0]

#         self.VFPAquisition	 = infile.read(2000)

#         self.Comment	 = infile.read(200)



    def read(self, fname, frame=None):
        """
        Read in header into self.header and
            the data   into self.data
        """
        self.header = {}
        self.resetvals()
        infile = self._open(fname, "rb")
        self._readheader(infile)
        # Compute image size
        try:
            self.dim1 = int(self.header['NumberOfRowsInFrame'])
            self.dim2 = int(self.header['NumberOfColsInFrame'])
            self.bpp = int(self.header['BitsPerPixel'])
        except:
            raise Exception("GE  file", str(fname) + \
                                "is corrupt, cannot read it")

        # More than one image can be saved in a GE file
        # Will only load the first one


        # Go to the beginning of the file
        infile.seek(0)
        infile.seek(self.header['HeaderSizeInBytes'] + self.header['UserHeaderSizeInBytes'])

        ReadBytes = self.dim1 * self.dim2 * (self.bpp / 8)
        block = infile.read(ReadBytes)
        block = numpy.fromstring(block, numpy.uint16)

        infile.close()

        try:
            self.data = numpy.reshape(block, [self.dim2, self.dim1])
        except:
            print len(block), self.dim2, self.dim1
            raise IOError, \
              'Size spec in GE-header does not match size of image data field'

        self.bytecode = self.data.dtype.type
        self.pilimage = None
        return self
