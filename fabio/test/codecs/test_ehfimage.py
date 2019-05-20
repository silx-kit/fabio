#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Project: Fable Input Output
#             https://github.com/silx-kit/fabio
#
#    Copyright (C) European Synchrotron Radiation Facility, Grenoble, France
#
#    Principal author:       Jérôme Kieffer (Jerome.Kieffer@ESRF.eu)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
# Unit tests
Reading extended edf files ("ehf-files") with fabio.module edfimage.py

16/05/2019 PB
"""
from __future__ import print_function, with_statement, division, absolute_import
import unittest
import os
import numpy
import shutil
import io
import logging

logger = logging.getLogger(__name__)

import fabio
from fabio.edfimage import edfimage
from ..utilstest import UtilsTest

#logging.basicConfig(level=logging.DEBUG)
#logging.basicConfig(level=logging.WARNING)
#logging.basicConfig(level=logging.INFO)
#logging.debug('This will get logged')
#logging.warning('This will get logged')
#logging.info('This will get logged')

#==========================================
def fopen(filename=None,frameno=None):
    header=None
    data=None
    frame=None
    logging.debug("fopen(filename={},frameno={})".format(filename,frameno))
    if filename:
        image=fabio.open(filename)
        if frameno is None:
            frameno=0

        nframes=image.nframes

        #if image.classname == "EdfImage":
        if hasattr(image,"npsdframes"):
            npsdframes=image.npsdframes
            nerrorframes=image.nerrorframes
        else:
            npsdframes=nframes
            nerrorframes=0

        if frameno >= npsdframes:
            logging.warning("Psd frame {} out of range: 0 <= {} < {}".format(frameno,frameno,npsdframes))

        if frameno <0:
            if -frameno > nerrorframes:
                logging.warning("Error frame {} out of range: {} <= {} < 0 ".format(frameno,-nerrorframes,frameno))
            frameno += nframes

        if frameno in range(nframes):
            if nframes>1:
                frame = image.getframe(frameno)
                data = frame.data
                header=frame.header
            else:
                # Single frame
                data = image.data
                header= image.header
            frame=fabio.fabioimage.FabioFrame(data=data, header=header)
        else:
            raise IOError("fopen: Cannot access frame: {} (0<=frame<{})".format(frameno, nframes))

    return(frame)

#============================================

ROOT = None

def test_00(self,filename,avglist=None,keylist=None):
    """
    Checks the shape of the data arrays.
    Compares the mean value of each data frame array, with the number given in avglist.
    filename: name of file to test
    avglist: list of average values for each frame, stops, if not equal
    keylist: list of keys to read, stops, if not available
    If avglist or keylist is shorter than frameno, the last value in the list is used.
    """
    global ROOT
    filename = os.path.join(ROOT, filename)
    image=fabio.open(filename)

    nframes=image.nframes

    if hasattr(image,"npsdframes"):
        npsdframes=image.npsdframes
        nerrorframes=image.nerrorframes
    else:
        npsdframes=image.nframes
        nerrorframes=0

    # To avoid warnings make different loops over psd data and error data
    #psd data
    for frameno in range(0,npsdframes):
        frame=fopen(filename,frameno)

        # check data shape
        counts=fabio.edfimage.get_data_counts(frame.shape)
        data_counts=fabio.edfimage.get_data_counts(frame.data.shape)

        self.assertEqual(counts, data_counts,"A:filename={},frameno={}: inconsistent data shapes: header.{},data.{}".
           format(filename,frameno,frame.shape,frame.data.shape))

        # calculate mean value
        sum=numpy.sum(frame.data)
        fmean=sum/counts

        logging.debug("filename={},frameno={},sum={},counts={},fmean={}".format(filename,frameno,sum,counts,fmean))

        # read known mean value from avglist
        if avglist is not None:
           if len(avglist)>frameno:
               avg=avglist[frameno]
           else:
               avg=avglist[-1]
           self.assertLessEqual(abs(fmean-avg),abs(fmean+avg)*5e-6,"B:filename={},frameno={}: unexpected average value: calculated {}, expected {}".
               format(filename,frameno,fmean,avg))

        # read a key to read from keylist
        if keylist is not None:
            if len(keylist)>frameno:
                key=keylist[frameno]
            else:
                key=keylist[-1]

            if key in frame.header:
               logging.debug("filename={}, frameno={}: '{}' = {}".format(filename,frameno,key,frame.header[key]))
            else:
               logging.debug("filename={}, frameno={}: '{}' = None".format(filename,frameno,key))

            self.assertIn(key,frame.header,"C:filename={},frameno={}: Missing expected header key '{}'".format(filename,frameno,key))

    #error data
    for frameno in range(0,nerrorframes):
        frame=fopen(filename,-frameno-1)

        # check data shape
        counts=fabio.edfimage.get_data_counts(frame.shape)
        data_counts=fabio.edfimage.get_data_counts(frame.data.shape)

        self.assertEqual(counts, data_counts,"D:filename={},frameno={}: inconsistent data shapes: header.{},data.{}".
           format(filename,frameno,frame.shape,frame.data.shape))

        # calculate mean value
        sum=numpy.sum(frame.data)
        fmean=sum/counts

        logging.debug("filename={},frameno={},sum={},counts={},fmean={}".format(filename,frameno,sum,counts,fmean))

        # read known mean value from avglist
        if avglist is not None:
           #error frames are taken from the end
           if len(avglist)>nframes-frameno-1:
               avg=avglist[nframes-frameno-1]
           else:
               avg=avglist[-1]
           self.assertLessEqual(abs(fmean-avg),abs(fmean+avg)*5e-6,"E:filename={},frameno={}: unexpected average value: calculated {}, expected {}".
               format(filename,frameno,fmean,avg))

        # read a key to read from keylist
        if keylist is not None:
            if len(keylist)>nframes-frameno-1:
                key=keylist[nframes-frameno-1]
            else:
                key=keylist[-1]

            if key in frame.header:
               logging.debug("filename={},frameno={}: key='{}'".format(filename,frameno,key,frame.header[key]))
            else:
               logging.debug("filename={},frameno={}: key=None".format(filename,frameno,key))

            self.assertIn(key,frame.header,"F:filename={},frameno={}: Missing expected header key '{}'".format(filename,frameno,key))

class EhfCases(unittest.TestCase):
    """
    Test the features of extended edf-files ("ehf-files").
    """

    def setUp(self):
        global ROOT
        unittest.TestCase.setUp(self)
        self.files = UtilsTest.resources.getdir("ehf_images2.tar.bz2")
        ROOT = os.path.join(self.files[0], "..")

    def test_edfblocktypes(self):
        """
        Test reading (gzipped) extended edf multi frame data files with and without a general block
        The files have been prepared with make_multiedfs.sh.
        The pixel values of each frame are equal to the frame number for checking reading the correct data.
        multi5.edf.gz:      5 frames without general block, preset frameno
        multi5+gblk.edf.gz: 5 frames starting with general block, preset to frameno,
                            DefaultKey added to the general block, it must be available in all headers
        multi5+err.edf.gz: 10 frames (5 psd, 5 error frames) without a general block, preset to frameno
            INFO:fabio.edfimage:Data stream is padded : 2560 > required 2400 bytes
                => unnecessary, it cannot be avoided, e.g. for saving byte arrays of odd length
        multi5_gzip.edf      : like multi5.edf.gz, but with internal compression
        multi5+gblk_gzip.edf : like multi5+gblk.edf.gz, but with internal compression
        multi5+err_gzip.edf  : like multi5+err.edf.gz, but with internal compression

        """
        test_00(self,"00_edfblocktypes/multi5.edf.gz",[0.,1.,2.,3.,4.])
        test_00(self,"00_edfblocktypes/multi5+gblk.edf.gz",[0.,1.,2.,3.,4.])
        test_00(self,"00_edfblocktypes/multi5+err.edf.gz",[0.,1.,2.,3.,4.,5.,6.,7.,8.,9.])
        test_00(self,"00_edfblocktypes/multi5+err_gzip.edf",[0.,1.,2.,3.,4.,5.,6.,7.,8.,9.])
        test_00(self,"00_edfblocktypes/multi5+gblk_gzip.edf",[0.,1.,2.,3.,4.])
        test_00(self,"00_edfblocktypes/multi5_gzip.edf",[0.,1.,2.,3.,4.])

    def test_edfsingle_raw_bf_gblk(self):
        """
        Reading an uncompressed edf-single-frame-file with references to data
        in externally saved dataframes.
        Check average data value, and verify that the key ExperimentInfo is
        correctly read from the general block.

        """
        avglist=[25743.2]
        keylist=["ExperimentInfo"]
        test_00(self,"01_single_raw_bf_gblk/pj19_frelon_00028_raw.ehf",avglist,keylist)

    def test_edfmulti_raw_bf_gblk(self):
        """
        Reading an uncompressed edf-multi-frame-file with references to data
        in externally saved dataframes and checking the average of each frame.
        Some header values are modified for checking the robustness.
        frames 0..16: Test reading from a multi frame edf file with links to
                      external binary files (ehf)
        frame 17:     Test reading without EDF_BinaryFileSize => must be
                      estimated from data size
        frame 18:     Test reading with EDF_BinaryFileSize bigger than required
                      => currently an unnecessary info is given
        """
        avglist=[9584.23, 9592.64, 9591.69, 9599.7, 9602.51, 9604.29, 9610.97, 9609.86, 9614.14, 9610.52, 9603.12, 9603.27, 9600.22, 9606.86, 9605.26, 9601.37, 9606.09, 9604.51, 9604.45, 9617.5]
        test_00(self,"02_multi_raw_bf_gblk/rh28a_saxs_00022_raw_binned.ehf",avglist)

    def test_edfmulti_raw_dark_raw_bf_gblk(self):
        """
        Linking data of several frames to different parts of a single external
        binary file.
        rh28a_saxs_00003_dark_binned.ehf:
          WARNING:fabio.edfimage:Under-short header frame 2: only 311 bytes
             => this should disappear when reading EDF_BlockBoundary
          INFO:fabio.edfimage:Data stream is padded : 29184 > required 28800 bytes
            => unnecessary, it cannot be avoided, e.g. for saving byte arrays of odd length
        rh28a_saxs_00003_raw_binned.ehf:
          INFO:fabio.edfimage:Data stream is padded : 29184 > required 28800 bytes
            => unnecessary, feature, e.g. for saving byte arrays of odd length
        """
        avglist=[2487.36, 2488.28, 2488.11]
        test_00(self,"03_multi_raw_dark_bf_gblk/rh28a_saxs_00003_dark_binned.ehf",avglist)
        avglist=[9651.25]
        test_00(self,"03_multi_raw_dark_bf_gblk/rh28a_saxs_00003_raw_binned.ehf",avglist)

    def test_edfsingle_raw_bf_gblk_gz(self):
        """
        Test reading gzipped data files linking to an external binary data file.
        Check that the extension .gz is added to the name of the external binary
        data file if it cannot be opened with the binary file name found in the
        header. Both files are gzipped.
        """
        avglist=[25743.2]
        test_00(self,"04_single_raw_bf_gblk_gz/pj19_frelon_00028_raw.ehf.gz",avglist)

    def test_edfsingle_raw_bf_gblk_gz(self):
        """
        Test reading gzipped data files linking to an external binary data file.
        Check that the extension .gz is added to the name of the external binary
        data file if it cannot be opened with the binary file name found in the
        header. The binary data file is not compressed.
        """
        avglist=[25743.2]
        test_00(self,"05_single_raw_bf_gblk_gz/pj19_frelon_00028_raw.ehf.gz",avglist)

    def test_edf6_single_raw_bf_gblk_gz(self):
        """
        Test reading gzipped data files linking to an external binary data file.
        Check that the extension .gz is added to the name of the external binary
        data file if it cannot be opened with the binary file name found in the
        header. Only the binary data file is gzipped.
        """
        avglist=[25743.2]
        test_00(self,"06_single_raw_bf_gblk_gz/pj19_frelon_00028_raw.ehf",avglist)

    def test_edfmulti_raw_bf_gblk_gz(self):
        """
        Test reading the files of the test test_edfmulti_raw_bf_gblk after
        gzipping.
        Test reading from multi frame files, like test_edfmulti_raw_bf_gblk, but
        but with all files gzipped.
        frames 0..16: Test reading from a multi frame edf file with links to
                      external binary files (ehf)
        frame 17:     Test reading without EDF_BinaryFileSize => should be
                      estimated from data size
        frame 18:     Test reading with EDF_BinaryFileSize bigger than required
                      => currently an unnecessary info is given
        frame 19:     Test reading with a wrong EDF_BinaryFileSize that excceeds
                      the real file size. => data must only be read to the end
                      of the binary data file.
        """
        avglist=[9584.23, 9592.64, 9591.69, 9599.7, 9602.51, 9604.29, 9610.97, 9609.86, 9614.14, 9610.52, 9603.12, 9603.27, 9600.22, 9606.86, 9605.26, 9601.37, 9606.09, 9604.51, 9604.45, 9617.5]
        test_00(self,"07_multi_raw_bf_gblk_gz/rh28a_saxs_00022_raw_binned.ehf.gz",avglist)

    def test_pitfalls(self):
        """
        multi5+headerblob_edf1.edf.gz
        multi5+headerblob+headerendinheader_edf1.edf.gz
        multi5+pitfalls_edf1.edf.gz
        multi5+headerblob_edf0.edf.gz
        multi5+headerblob+headerendinheader_edf0.edf.gz
        multi5+pitfalls_edf0.edf.gz
        """

        # edf1 file => must always work
        avglist=[0,1,2,3,4]
        test_00(self,"08_pitfalls/multi5+pitfalls_edf1.edf.gz",avglist)

        # edf1 file with header end pattern in binary blob => must always work
        avglist=[18312,18312,18312,18312,18312]
        test_00(self,"08_pitfalls/multi5+headerblob_edf1.edf.gz",avglist)

        # edf1 file with header end pattern in Title value and binary blob
        # => must always work
        test_00(self,"08_pitfalls/multi5+headerblob+headerendinheader_edf1.edf.gz",avglist)

        # edf0 file => must always work
        avglist=[0,1,2,3,4]
        test_00(self,"08_pitfalls/multi5+pitfalls_edf0.edf.gz",avglist)

        # edf0 file with header end pattern in binary blob => must always work
        avglist=[18312,18312,18312,18312,18312]
        test_00(self,"08_pitfalls/multi5+headerblob_edf0.edf.gz",avglist)

        # edf0 file with header end pattern in Title value and binary blob
        # => usually fails, because the header end pattern is searched
        # by parsing each byte of the header.
        # The next test usually fails, because the value of the header key
        # "Title" contains a header end pattern.
        # There is no safe way of reading such files.
        # When writing the files it must be checked that no special
        # characters are written to header values, especially
        # not '{', '}', ';'.
        # Searching the end_marker in a header in steps of BLOCKSIZE
        # instead of searching through the whole header byte for
        # byte would allow reading most of such files, but success is not
        # guaranteed. => Do not write special character to the header
        # test_00(self,"08_pitfalls/multi5+headerblob+headerendinheader_edf0.edf.gz",avglist)

    def test_special(self):
        """
        09_special/face_ok.edf.gz
        09_special/face_headerendatboundary1.edf.gz
        09_special/face_headerendatboundary2.edf.gz
        09_special/face_headerendatboundary3.edf.gz
        09_special/face_tooshort.edf.gz
        """

        avglist=[0.178897]
        test_00(self,"09_special/face_ok.edf.gz",avglist)

        # The next 3 tests check that edf files can be
        # read where the header end pattern spreads over a
        # BLOCKSIZE boundary. This is usually not a problem
        # for header blocks that are padded to multiples of BLOCKSIZE
        # and that are aligned to BLOCKSIZE boundaries.
        # This error can happen if edf header are modified with
        # an editor.
        # The following tests will fail if distributed  header end
        # patterns are not recognized.
        avglist=[0.178897]
        # header end character '}' at BLOCKSIZE-1 followed by '\n' at BLOCKSIZE
        test_00(self,"09_special/face_headerendatboundary1.edf.gz",avglist)
        # first part of header end pattern '}\r' at BLOCKSIZE-2 followed by '\n' at BLOCKSIZE
        test_00(self,"09_special/face_headerendatboundary2.edf.gz",avglist)
        # header end character '}' at BLOCKSIZE-1 followed by '\n' at BLOCKSIZE
        test_00(self,"09_special/face_headerendatboundary3.edf.gz",avglist)

        # Here, the binary blob is too short
        # like 09_special/face_headerendatboundary1.edf.gz, but in addition
        # the binary blob is too short by 1 byte.
        # Currently, an error message is shown and the data
        # is truncated
        # avglist=[0.178897]
        # test_00(self,"09_special/face_tooshort.edf.gz",avglist)


def suite():
    loadTests = unittest.defaultTestLoader.loadTestsFromTestCase
    testsuite = unittest.TestSuite()
    testsuite.addTest(loadTests(EhfCases))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
