#!/usr/bin/env python

"""
Reads Oxford Diffraction Sapphire 3 images

Authors: Henning O. Sorensen & Erik Knudsen
         Center for Fundamental Research: Metal Structures in Four Dimensions
         Risoe National Laboratory
         Frederiksborgvej 399
         DK-4000 Roskilde
         email:erik.knudsen@risoe.dk

        + Jon Wright, ESRF

"""

import numpy.oldnumeric as Numeric, logging
from fabio.fabioimage import fabioimage

DETECTOR_TYPES = {0: 'Sapphire/KM4CCD (1x1: 0.06mm, 2x2: 0.12mm)',
1: 'Sapphire2-Kodak (1x1: 0.06mm, 2x2: 0.12mm)',
2: 'Sapphire3-Kodak (1x1: 0.03mm, 2x2: 0.06mm, 4x4: 0.12mm)',
3: 'Onyx-Kodak (1x1: 0.06mm, 2x2: 0.12mm, 4x4: 0.24mm)'}


class OXDimage(fabioimage):
    def _readheader(self,infile):
        
        infile.seek(0)
        
        # Ascii header part 512 byes long 
        self.header['Header Version'] = infile.readline()[:-2]
        block = infile.readline()
        self.header['Compression'] = block[12:15]
        block = infile.readline()
        self.header['NX'] = int(block[3:7])
        self.header['NY'] = int(block[11:15])
        self.header['OI'] = int(block[19:26])
        self.header['OL'] = int(block[30:37])
        block = infile.readline()
        self.header['Header Size In Bytes'] = int(block[8:15])
        #self.header['NG'] = int(block[19:26])
        #self.header['NK'] = int(block[30:37])
        #self.header['NS'] = int(block[41:48])
        #self.header['NH'] = int(block[52:59])
        block = infile.readline()
        #self.header['NSUPPLEMENT'] = int(block[12:19])
        block = infile.readline()
        self.header['Time'] = block[5:29]

        # Skip to general section (NG) 512 byes long <<<<<<"
        infile.seek(256) 
        block = infile.read(512)
        self.header['Binning in x'] =  Numeric.fromstring(block[0:2],Numeric.UInt16)[0]
        self.header['Binning in y'] =  Numeric.fromstring(block[2:4],Numeric.UInt16)[0]
        self.header['Detector size x'] =  Numeric.fromstring(block[22:24],Numeric.UInt16)[0]
        self.header['Detector size y'] =  Numeric.fromstring(block[24:26],Numeric.UInt16)[0]
        self.header['Pixels in x'] =  Numeric.fromstring(block[26:28],Numeric.UInt16)[0]
        self.header['Pixels in y'] =  Numeric.fromstring(block[28:30],Numeric.UInt16)[0]
        self.header['No of pixels'] =  Numeric.fromstring(block[36:40],Numeric.UInt32)[0]

        # Speciel section (NS) 768 bytes long
        block = infile.read(768)
        self.header['Gain'] =  Numeric.fromstring(block[56:64],Numeric.Float)[0]
        self.header['Overflows flag'] =  Numeric.fromstring(block[464:466],Numeric.Int16)[0]
        self.header['Overflow after remeasure flag'] =  Numeric.fromstring(block[466:468],Numeric.Int16)[0]
        self.header['Overflow threshold'] =  Numeric.fromstring(block[472:476],Numeric.Int32)[0]
        self.header['Exposure time in sec'] =  Numeric.fromstring(block[480:488],Numeric.Float)[0]
        self.header['Overflow time in sec'] =  Numeric.fromstring(block[488:496],Numeric.Float)[0]
        self.header['Monitor counts of raw image 1'] =  Numeric.fromstring(block[528:532],Numeric.Int32)[0]
        self.header['Monitor counts of raw image 2'] =  Numeric.fromstring(block[532:536],Numeric.Int32)[0]
        self.header['Monitor counts of overflow raw image 1'] =  Numeric.fromstring(block[536:540],Numeric.Int32)[0]
        self.header['Monitor counts of overflow raw image 2'] =  Numeric.fromstring(block[540:544],Numeric.Int32)[0]
        self.header['Unwarping'] =  Numeric.fromstring(block[544:548],Numeric.Int32)[0]
        self.header['Detector type'] =  DETECTOR_TYPES[Numeric.fromstring(block[548:552],Numeric.Int32)[0]]
        self.header['Real pixel size x (mm)'] =  Numeric.fromstring(block[568:576],Numeric.Float)[0]
        self.header['Real pixel size y (mm)'] =  Numeric.fromstring(block[576:584],Numeric.Float)[0]

        # KM4 goniometer section (NK) 1024 bytes long
        block = infile.read(1024)
        # Spatial correction file
        self.header['Spatial correction file'] = block[26:272]
        self.header['Spatial correction file date'] = block[0:26]
        # Angles are in steps due to stepper motors - conversion factor RAD
        # angle[0] = omega, angle[1] = theta, angle[2] = kappa, angle[3] = phi,   
        start_angles_step = Numeric.fromstring(block[284:304],Numeric.Int32)
        end_angles_step = Numeric.fromstring(block[324:344],Numeric.Int32)
        step2rad = Numeric.fromstring(block[368:408],Numeric.Float)
        # calc angles
        start_angles_deg = start_angles_step*step2rad*180.0/Numeric.pi
        
        end_angles_deg = end_angles_step*step2rad*180.0/Numeric.pi
        self.header['Omega start in deg'] = start_angles_deg[0]
        self.header['Theta start in deg'] = start_angles_deg[1]
        self.header['Kappa start in deg'] = start_angles_deg[2]
        self.header['Phi start in deg'] = start_angles_deg[3]
        self.header['Omega end in deg'] = end_angles_deg[0]
        self.header['Theta end in deg'] = end_angles_deg[1]
        self.header['Kappa end in deg'] = end_angles_deg[2]
        self.header['Phi end in deg'] = end_angles_deg[3]

        zero_correction_soft_step = Numeric.fromstring(block[512:532],Numeric.Int32)
        zero_correction_soft_deg = zero_correction_soft_step*step2rad*180.0/Numeric.pi
        self.header['Omega zero corr. in deg'] = zero_correction_soft_deg[0]
        self.header['Theta zero corr. in deg'] = zero_correction_soft_deg[1]
        self.header['Kappa zero corr. in deg'] = zero_correction_soft_deg[2]
        self.header['Phi zero corr. in deg'] = zero_correction_soft_deg[3]
        # Beam rotation about e2,e3
        self.header['Beam rot in deg (e2)'] = Numeric.fromstring(block[552:560],Numeric.Float)[0]
        self.header['Beam rot in deg (e3)'] = Numeric.fromstring(block[560:568],Numeric.Float)[0]
        # Wavelenghts alpha1, alpha2, beta
        self.header['Wavelength alpha1'] = Numeric.fromstring(block[568:576],Numeric.Float)[0]
        self.header['Wavelength alpha2'] = Numeric.fromstring(block[576:584],Numeric.Float)[0]
        self.header['Wavelength alpha'] = Numeric.fromstring(block[584:592],Numeric.Float)[0]
        self.header['Wavelength beta'] = Numeric.fromstring(block[592:600],Numeric.Float)[0]

        # Detector tilts around e1,e2,e3 in deg
        self.header['Detector tilt e1 in deg'] = Numeric.fromstring(block[640:648],Numeric.Float)[0]
        self.header['Detector tilt e2 in deg'] = Numeric.fromstring(block[648:656],Numeric.Float)[0]
        self.header['Detector tilt e3 in deg'] = Numeric.fromstring(block[656:664],Numeric.Float)[0]

        
        # Beam center
        self.header['Beam center x'] = Numeric.fromstring(block[664:672],Numeric.Float)[0]
        self.header['Beam center y'] = Numeric.fromstring(block[672:680],Numeric.Float)[0]
        # Angle (alpha) between kappa rotation axis and e3 (ideally 50 deg)
        self.header['Alpha angle in deg'] = Numeric.fromstring(block[672:680],Numeric.Float)[0]
        # Angle (beta) between phi rotation axis and e3 (ideally 0 deg)
        self.header['Beta angle in deg'] = Numeric.fromstring(block[672:680],Numeric.Float)[0]
        
        # Detector distance
        self.header['Distance in mm'] = Numeric.fromstring(block[712:720],Numeric.Float)[0]
        # Statistics section (NS) 512 bytes long
        block = infile.read(512)
        self.header['Stat: Min '] = Numeric.fromstring(block[0:4],Numeric.Int32)[0]
        self.header['Stat: Max '] = Numeric.fromstring(block[4:8],Numeric.Int32)[0]
        self.header['Stat: Average '] =  Numeric.fromstring(block[24:32],Numeric.Float)[0]
        self.header['Stat: Stddev '] =  Numeric.sqrt(Numeric.fromstring(block[32:40],Numeric.Float)[0])
        self.header['Stat: Skewness '] =  Numeric.fromstring(block[40:48],Numeric.Float)[0]

        # History section (NH) 2048 bytes long - only reads first 256 bytes
        block = infile.read(256)
        self.header['Flood field image'] = block[99:126]

    def read(self, fname):
        """
        Read in header into self.header and
            the data   into self.data
        """
        self.header = {}
        self.resetvals()
        infile = self._open(fname)
        self._readheader(infile)

        infile.seek(self.header['Header Size In Bytes'])

        # Compute image size
        try:
            self.dim1 = int(self.header['NX'])
            self.dim2 = int(self.header['NY'])
        except:
            raise Exception("Oxford  file", str(fname) + \
                                "is corrupt, cannot read it")
        #
        if self.header['Compression'] == 'TY1':
            #Compressed with the KM4CCD compression
            bytecode = Numeric.UInt8
            self.bpp = len(Numeric.array(0, bytecode).tostring())
            ReadBytes = self.dim1 * self.dim2 * self.bpp 
            diffs = infile.read(ReadBytes)
            diffs = Numeric.fromstring(diffs,bytecode)
            offset = -127
            diffs = diffs.astype(Numeric.Int32)+offset
            
            if self.header['OI'] > 0:
                bytecode = Numeric.Int16
                self.bpp = len(Numeric.array(0, bytecode).tostring())
                ReadBytes = self.header['OI'] * self.bpp 
                over_short = infile.read(ReadBytes)
                over_short = Numeric.fromstring(over_short,bytecode)
            if self.header['OL'] > 0:
                bytecode = Numeric.Int32
                self.bpp = len(Numeric.array(0, bytecode).tostring())
                ReadBytes = self.header['OL'] * self.bpp 
                over_long = infile.read(ReadBytes)
                block = Numeric.fromstring(over_long,bytecode)
            block = diffs.copy()
            old_val = 0
            js = 0
            jl = 0
            for i in range(self.dim1*self.dim2):
                if diffs[i] < 127:
                    d = diffs[i]
                elif diffs[i] == 127:
                    d = over_short[js]
                    js = js + 1
                elif diffs[i] == 128:
                    d = over_long[jl]
                    jl = jl + 1
                old_val  = old_val + d
                block[i] = old_val
        else:
            bytecode = Numeric.Int32
            self.bpp = len(Numeric.array(0, bytecode).tostring())
            ReadBytes = self.dim1 * self.dim2 * self.bpp 
            block = Numeric.fromstring(infile.read(ReadBytes),bytecode)
        
        #
        infile.close()

        try:
            self.data = Numeric.reshape(block,[self.dim2, self.dim1])
        except:
            print len(block), self.dim2, self.dim1
            raise IOError, \
              'Size spec in OD-header does not match size of image data field'

        self.bytecode = self.data.dtype.char
        self.pilimage = None
        return self
