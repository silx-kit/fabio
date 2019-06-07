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
Reading edf files as originally specified by expg with fabio.module edfimage.py

07/06/2019 PB
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


class EdfBlockBoundaryCases(unittest.TestCase):
    """
    Test some special cases
    """

    def setUp(self):
        global ROOT
        unittest.TestCase.setUp(self)
        self.files = UtilsTest.resources.getdir("ehf_images2.tar.bz2")
        ROOT = os.path.join(self.files[0], "..")

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
    testsuite.addTest(loadTests(EdfBlockBoundaryCases))
    return testsuite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())

