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

import numpy as N, logging
from fabioimage import fabioimage

DETECTOR_TYPES = {0: 'Sapphire/KM4CCD (1x1: 0.06mm, 2x2: 0.12mm)',
1: 'Sapphire2-Kodak (1x1: 0.06mm, 2x2: 0.12mm)',
2: 'Sapphire3-Kodak (1x1: 0.03mm, 2x2: 0.06mm, 4x4: 0.12mm)',
3: 'Onyx-Kodak (1x1: 0.06mm, 2x2: 0.12mm, 4x4: 0.24mm)',
4: 'Unknown Oxford diffraction detector'}


class OXDimage(fabioimage):
    def _readheader(self, infile):

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
        self.header['Binning in x'] = N.fromstring(block[0:2], N.uint16)[0]
        self.header['Binning in y'] = N.fromstring(block[2:4], N.uint16)[0]
        self.header['Detector size x'] = N.fromstring(block[22:24], N.uint16)[0]
        self.header['Detector size y'] = N.fromstring(block[24:26], N.uint16)[0]
        self.header['Pixels in x'] = N.fromstring(block[26:28], N.uint16)[0]
        self.header['Pixels in y'] = N.fromstring(block[28:30], N.uint16)[0]
        self.header['No of pixels'] = N.fromstring(block[36:40], N.uint32)[0]

        # Speciel section (NS) 768 bytes long
        block = infile.read(768)
        self.header['Gain'] = N.fromstring(block[56:64], N.float)[0]
        self.header['Overflows flag'] = N.fromstring(block[464:466], N.int16)[0]
        self.header['Overflow after remeasure flag'] = N.fromstring(block[466:468], N.int16)[0]
        self.header['Overflow threshold'] = N.fromstring(block[472:476], N.int32)[0]
        self.header['Exposure time in sec'] = N.fromstring(block[480:488], N.float)[0]
        self.header['Overflow time in sec'] = N.fromstring(block[488:496], N.float)[0]
        self.header['Monitor counts of raw image 1'] = N.fromstring(block[528:532], N.int32)[0]
        self.header['Monitor counts of raw image 2'] = N.fromstring(block[532:536], N.int32)[0]
        self.header['Monitor counts of overflow raw image 1'] = N.fromstring(block[536:540], N.int32)[0]
        self.header['Monitor counts of overflow raw image 2'] = N.fromstring(block[540:544], N.int32)[0]
        self.header['Unwarping'] = N.fromstring(block[544:548], N.int32)[0]
        self.header['Detector type'] = DETECTOR_TYPES[N.fromstring(block[548:552], N.int32)[0]]
        self.header['Real pixel size x (mm)'] = N.fromstring(block[568:576], N.float)[0]
        self.header['Real pixel size y (mm)'] = N.fromstring(block[576:584], N.float)[0]

        # KM4 goniometer section (NK) 1024 bytes long
        block = infile.read(1024)
        # Spatial correction file
        self.header['Spatial correction file'] = block[26:272]
        self.header['Spatial correction file date'] = block[0:26]
        # Angles are in steps due to stepper motors - conversion factor RAD
        # angle[0] = omega, angle[1] = theta, angle[2] = kappa, angle[3] = phi,   
        start_angles_step = N.fromstring(block[284:304], N.int32)
        end_angles_step = N.fromstring(block[324:344], N.int32)
        step2rad = N.fromstring(block[368:408], N.float)
        # calc angles
        start_angles_deg = start_angles_step * step2rad * 180.0 / N.pi

        end_angles_deg = end_angles_step * step2rad * 180.0 / N.pi
        self.header['Omega start in deg'] = start_angles_deg[0]
        self.header['Theta start in deg'] = start_angles_deg[1]
        self.header['Kappa start in deg'] = start_angles_deg[2]
        self.header['Phi start in deg'] = start_angles_deg[3]
        self.header['Omega end in deg'] = end_angles_deg[0]
        self.header['Theta end in deg'] = end_angles_deg[1]
        self.header['Kappa end in deg'] = end_angles_deg[2]
        self.header['Phi end in deg'] = end_angles_deg[3]

        zero_correction_soft_step = N.fromstring(block[512:532], N.int32)
        zero_correction_soft_deg = zero_correction_soft_step * step2rad * 180.0 / N.pi
        self.header['Omega zero corr. in deg'] = zero_correction_soft_deg[0]
        self.header['Theta zero corr. in deg'] = zero_correction_soft_deg[1]
        self.header['Kappa zero corr. in deg'] = zero_correction_soft_deg[2]
        self.header['Phi zero corr. in deg'] = zero_correction_soft_deg[3]
        # Beam rotation about e2,e3
        self.header['Beam rot in deg (e2)'] = N.fromstring(block[552:560], N.float)[0]
        self.header['Beam rot in deg (e3)'] = N.fromstring(block[560:568], N.float)[0]
        # Wavelenghts alpha1, alpha2, beta
        self.header['Wavelength alpha1'] = N.fromstring(block[568:576], N.float)[0]
        self.header['Wavelength alpha2'] = N.fromstring(block[576:584], N.float)[0]
        self.header['Wavelength alpha'] = N.fromstring(block[584:592], N.float)[0]
        self.header['Wavelength beta'] = N.fromstring(block[592:600], N.float)[0]

        # Detector tilts around e1,e2,e3 in deg
        self.header['Detector tilt e1 in deg'] = N.fromstring(block[640:648], N.float)[0]
        self.header['Detector tilt e2 in deg'] = N.fromstring(block[648:656], N.float)[0]
        self.header['Detector tilt e3 in deg'] = N.fromstring(block[656:664], N.float)[0]


        # Beam center
        self.header['Beam center x'] = N.fromstring(block[664:672], N.float)[0]
        self.header['Beam center y'] = N.fromstring(block[672:680], N.float)[0]
        # Angle (alpha) between kappa rotation axis and e3 (ideally 50 deg)
        self.header['Alpha angle in deg'] = N.fromstring(block[672:680], N.float)[0]
        # Angle (beta) between phi rotation axis and e3 (ideally 0 deg)
        self.header['Beta angle in deg'] = N.fromstring(block[672:680], N.float)[0]

        # Detector distance
        self.header['Distance in mm'] = N.fromstring(block[712:720], N.float)[0]
        # Statistics section (NS) 512 bytes long
        block = infile.read(512)
        self.header['Stat: Min '] = N.fromstring(block[0:4], N.int32)[0]
        self.header['Stat: Max '] = N.fromstring(block[4:8], N.int32)[0]
        self.header['Stat: Average '] = N.fromstring(block[24:32], N.float)[0]
        self.header['Stat: Stddev '] = N.sqrt(N.fromstring(block[32:40], N.float)[0])
        self.header['Stat: Skewness '] = N.fromstring(block[40:48], N.float)[0]

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
            bytecode = N.uint8
            self.bpp = len(N.array(0, bytecode).tostring())
            ReadBytes = self.dim1 * self.dim2 * self.bpp
            diffs = infile.read(ReadBytes)
            diffs = N.fromstring(diffs, bytecode)
            offset = -127
            diffs = diffs.astype(N.int32) + offset

            if self.header['OI'] > 0:
                bytecode = N.int16
                self.bpp = len(N.array(0, bytecode).tostring())
                ReadBytes = self.header['OI'] * self.bpp
                over_short = infile.read(ReadBytes)
                over_short = N.fromstring(over_short, bytecode)
            if self.header['OL'] > 0:
                bytecode = N.int32
                self.bpp = len(N.array(0, bytecode).tostring())
                ReadBytes = self.header['OL'] * self.bpp
                over_long = infile.read(ReadBytes)
                over_long = N.fromstring(over_long, bytecode)
            block = diffs.copy()
            old_val = 0
            js = 0
            jl = 0
            print 'OVER_SHORT: ', block.dtype

            for i in range(self.dim1 * self.dim2):
                if diffs[i] < 127:
                    #print 'DIFF < 127:' , diffs[i] 
                    d = diffs[i]
                elif diffs[i] == 127:
                    #print 'DIFF == 127:' , diffs[i] 
                    d = over_short[js]
                    #print 'd ' , d
                    js = js + 1
                elif diffs[i] == 128:
                    #print 'DIFF == 128:' , diffs[i] 
                    d = over_long[jl]
                    jl = jl + 1
                old_val = old_val + d
                block[i] = old_val
        else:
            bytecode = N.int32
            self.bpp = len(N.array(0, bytecode).tostring())
            ReadBytes = self.dim1 * self.dim2 * self.bpp
            block = N.fromstring(infile.read(ReadBytes), bytecode)

        print 'OVER_SHORT2: ', block.dtype
        print (block < 0).sum()
        #
        infile.close()
        print "BYTECODE", bytecode
        try:
            # avoid int64 for x86_64 with astype
            bytecode = N.int32

            self.data = N.reshape(block.astype(bytecode), [self.dim2, self.dim1])
            #self.data = N.reshape(block,[self.dim2, self.dim1])
        except:
            print len(block), self.dim2, self.dim1
            raise IOError, \
              'Size spec in OD-header does not match size of image data field'

        self.bytecode = self.data.dtype.type
        self.pilimage = None
        return self
