#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Project: Fast Azimuthal integration
#             https://github.com/silx-kit/pyFAI
#
#
#    Copyright (C) European Synchrotron Radiation Facility, Grenoble, France
#
#    Authors: Gael Goret <gael.goret@esrf.fr>
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#  .
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#  .
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.
"""
Portable diffraction images viewer/converter

* Written in Python, it combines the functionalities of the I/O library fabIO
  with a user friendly Qt GUI.
* Image converter is also a light viewer based on the visualization tool
  provided by the module matplotlib.
"""

__version__ = "1.0"
__author__ = "Gaël Goret, Jérôme Kieffer"
__copyright__ = "2015 ESRF"
__licence__ = "GPL"

import sys
import os
import time

from . import _qt as qt
from ._matplotlib import FigureCanvasQTAgg
from ._matplotlib import NavigationToolbar2QT
from matplotlib.figure import Figure

import numpy
numpy.seterr(divide='ignore')

import fabio

from fabio.nexus import Nexus
from argparse import ArgumentParser

output_format = ['*.bin', '*.cbf', '*.edf', '*.h5', '*.img',
                 '*.mar2300', '*.mar3450', '*.marccd', '*.tiff', "*.sfrm"]


class AppForm(qt.QMainWindow):

    def __init__(self, parent=None):

        # Main window
        qt.QMainWindow.__init__(self, parent)
        self.setWindowTitle('FabIO Viewer')
        self.setSizePolicy(qt.QSizePolicy().Expanding, qt.QSizePolicy().Expanding)
        # Menu and widget
        self.create_menu()
        self.create_main_frame()
        self.create_status_bar()

        # Active Data
        self.data = numpy.array([])
        self.header = []

        # Data Series
        self.imgDict = {}
        self.data_series = []
        self.header_series = []
        self.sequential_file_list = []
        self.sequential_file_dict = {}

        # Miscellaneous
        self.mask = None
        self.transform_data_series = False
        self.transform_list = []
        self.sequential_file_mode = False
        self.h5_loaded = False
        self.counter_format = '%03d'

    def format_header(self, d):
        """
        :param d: dict containing headers
        :return: formated string
        """
        keys = list(d.keys())
        keys.sort()
        res = " \n".join(['%s: %s' % (k, d[k]) for k in keys]) + " \n"
        return res

    def _open(self, filename):
        """Returns a fabio image if the file can be loaded, else display a
        dialog to help decoding the file. Else return None."""
        try:
            img = fabio.open(filename)
        except Exception as _:
            message = 'Automatic format recognition procedure failed or '\
                'pehaps you are trying to open a binary data block...\n\n'\
                'Switch to manual procedure.'
            qt.QMessageBox.warning(self, 'Message', message)
            dial = BinDialog(self)
            dim1, dim2, offset, bytecode, endian = dial.exec_()
            if dim1 is not None and dim2 is not None:
                if endian == 'Short':
                    endian = '<'
                else:
                    endian = '>'
                img = fabio.binaryimage.binaryimage()
                img.read(filename, dim1, dim2, offset, bytecode, endian)
                img.header = {'Info': 'No header information available in binary data blocks'}
            else:
                return
        return img

    def open_data_series(self, series=None):
        if not series:
            series = qt.QFileDialog.getOpenFileNames(self, 'Select and open series of files')
            if isinstance(series, tuple):
                # PyQt5 compatibility
                series = series[0]

        series = [str(f) for f in list(series)]
        total = len(series)
        if len(series) != 0:
            self.data_series = []
            self.header_series = []
            self.sequential_file_list = []
            iid = 0
            self.imgDict = {}
            self.sequential_file_dict = {}
            self.images_list.clear()
            self.imagelistWidget.clear()
            self.headerTextEdit.clear()
            self.axes.clear()
            self.canvas.draw()
            self.h5_loaded = False
            for fname in series:
                if fname:
                    extract_fname = self.extract_fname_from_path(fname)
                    if self.sequential_file_mode:
                        self.statusBar().showMessage('Adding path %s to batch image list, please wait...' % fname)
                        self.log.appendPlainText('Adding path %s to batch image list' % fname)
                        qt.QCoreApplication.processEvents()
                        self.imagelistWidget.addItem(extract_fname)
                        self.sequential_file_list += [extract_fname]
                        self.sequential_file_dict[extract_fname] = fname
                        iid += 1
                    else:
                        self.statusBar().showMessage('Opening file %s, please wait...' % fname)
                        self.log.appendPlainText('Opening file %s' % fname)
                        qt.QCoreApplication.processEvents()
                        img = self._open(fname)
                        if img is None:
                            continue
                        if img.nframes > 1:
                            for img_idx in range(img.nframes):
                                frame = img.getframe(img_idx)
                                self.data_series.append(frame.data[:])
                                self.header_series.append(frame.header.copy())
                                frame_name = "%s # %i" % (extract_fname, img_idx)
                                self.images_list.addItem(frame_name)
                                self.imagelistWidget.addItem(frame_name)
                                self.imgDict[frame_name] = iid
                                self.sequential_file_list += [frame_name]
                                self.sequential_file_dict[frame_name] = fname
                                iid += 1
                        else:
                            self.data_series.append(img.data[:])
                            self.header_series.append(img.header.copy())
                            extract_fname = self.extract_fname_from_path(fname)
                            self.images_list.addItem(extract_fname)
                            self.imagelistWidget.addItem(extract_fname)
                            self.imgDict[extract_fname] = iid
                            self.sequential_file_list += [extract_fname]
                            self.sequential_file_dict[extract_fname] = fname
                            iid += 1
                self.progressBar.setValue(int((iid + 1) / total * 100.))
            self.statusBar().clearMessage()
            self.progressBar.setValue(0)
            self.log.appendPlainText('Opening procedure: Complete')
            if self.data_series:
                self.select_new_image(None, imgID=0)

    def open_h5_data_series(self):  # TODO batch mode compatibility
        fname = qt.QFileDialog.getOpenFileName(self, 'Select and open series of files')
        if isinstance(fname, tuple):
            # PyQt5 compatibility
            fname = fname[0]

        fname = str(fname)
        self.h5_loaded = True
        if self.filecheckBox.checkState():
            self.filecheckBox.stateChanged.disconnect()
            self.filecheckBox.setCheckState(False)
            self.sequential_file_mode = False
            self.filecheckBox.stateChanged.connect(self.sequential_option)
            message = 'Sequential file mode is not compatible with hdf5 input file: option removed'
            qt.QMessageBox.warning(self, 'Message', message)
        if fname:
            self.data_series = []
            self.header_series = []
            self.sequential_file_list = []
            self.sequential_file_dict = {}
            self.imagelistWidget.clear()
            self.headerTextEdit.clear()
            with Nexus(fname, 'r') as nxs:
                entry = nxs.get_entries()[0]
                nxdata = nxs.get_class(entry, class_type="NXdata")[0]
                dataset = nxdata.get("data", numpy.zeros(shape=(1, 1, 1)))
                total = dataset.shape[0]
                imgDict = {}
                extract_fname = os.path.basename(os.path.splitext(fname)[0])
                self.images_list.clear()
                safeiid = 0
                for iid in range(total):
                    self.progressBar.setValue(int((iid + 1.0) / total * 100.))
                    self.log.appendPlainText('Extracting data from hdf5 archive, image number %d' % iid)
                    qt.QCoreApplication.processEvents()
                    self.data_series.append(dataset[iid])
                    self.header_series += [{'Info': 'No header information available in hdf5 Archive'}]
                    imgDict[extract_fname + str(iid)] = safeiid
                    self.images_list.addItem(extract_fname + str(iid))
                    safeiid += 1
            self.statusBar().clearMessage()
            self.progressBar.setValue(0)
            self.log.appendPlainText('Hdf5 Extraction: Complete')
            self.imgDict = imgDict.copy()
        if self.data_series:
            self.select_new_image(None, imgID=0)

    def extract_fname_from_path(self, name):
        posslash = name.rfind("/")
        if posslash > -1:
            return name[posslash + 1:]
        else:
            return name

    defaultSaveFilter = ""\
        "binary data block (*.bin);;"\
        "cbf image (*.cbf);;"\
        "edf image (*.edf);;"\
        "oxford diffraction image (*.img);;"\
        "mar2300 image(*.mar2300);;"\
        "mar3450 image (*.mar3450);;"\
        "marccd image (*.marccd));;"\
        "tiff image (*.tiff);;"\
        "bruker image (*.sfrm)"

    def _getSaveFileNameAndFilter(self, parent=None, caption='', directory='',
                                  filter=''):
        dialog = qt.QFileDialog(parent, caption=caption, directory=directory)
        dialog.setAcceptMode(qt.QFileDialog.AcceptSave)
        dialog.setNameFilter(filter)
        result = dialog.exec_()
        if not result:
            return "", ""
        return dialog.selectedFiles()[0], dialog.selectedNameFilter()

    def save_as(self):
        info = self._getSaveFileNameAndFilter(self, "Save active image as",
                                              qt.QDir.currentPath(),
                                              filter=self.tr(self.defaultSaveFilter))
        if self.data.any():
            if str(info[0]) != '' and str(info[1]) != '':
                format_ = self.extract_format_from_string(str(info[1]))
                fname = self.add_extention_if_absent(str(info[0]), format_)
                self.convert_and_write(fname, format_, self.data, self.header)
        else:
            if str(info[0]) != '' and str(info[1]) != '':
                message = "Could not save image as file if no data have been loaded"
                qt.QMessageBox.warning(self, 'Warning', message)

    def save_data_series_as_multiple_file(self):
        info = self._getSaveFileNameAndFilter(self, "Save data series as multiple files",
                                              qt.QDir.currentPath(),
                                              filter=self.tr(self.defaultSaveFilter))
        if self.data_series or self.sequential_file_list:
            if str(info[0]) != '' and str(info[1]) != '':
                format_ = self.extract_format_from_string(str(info[1]))
                fname = self.os.path.splitext(str(info[0]))[0]
                self.convert_and_write_multiple_files(fname, format_)
        else:
            if str(info[0]) != '' and str(info[1]) != '':
                message = "Could not save image as file if no data have been loaded"
                qt.QMessageBox.warning(self, 'Warning', message)

    def save_data_series_as_singlehdf(self):
        info = self._getSaveFileNameAndFilter(self, "Save data series as single high density file",
                                              qt.QDir.currentPath(),
                                              filter=self.tr("HDF5 archive (*.h5)"))
        if self.data_series or self.sequential_file_list:
            if str(info[0]) != '' and str(info[1]) != '':
                format_ = self.extract_format_from_string(str(info[1]))
                fname = self.add_extention_if_absent(str(info[0]), format_)
                if format_ == '*.h5':
                    self.convert_and_save_to_h5(fname)
                else:
                    qt.QMessageBox.warning(self, 'Warning', "Unknown format: %s" % format_)
                    return
        else:
            if str(info[0]) != '' and str(info[1]) != '':
                message = "Could not save image as file if no data have been loaded"
                qt.QMessageBox.warning(self, 'Warning', message)

    def convert_and_save_to_h5(self, fname):
        """
        Save a stack as Nexus entry (create a new entry in the file each time)
        """
        with Nexus(fname) as nxs:
            entry = nxs.new_entry(entry="entry", program_name="fabio_viewer", title="FabIO Viewer")
            nxdata = nxs.new_class(entry, "fabio", class_type="NXdata")
            # Read shape:
            if self.sequential_file_mode:
                total = len(self.sequential_file_list)
                tmpfname = self.sequential_file_dict[self.sequential_file_list[0]]
                img = self._open(tmpfname)
                if img is None:
                    return
                data = img.data
            else:
                total = len(self.data_series)
                data = self.data_series[0]
            if self.transform_data_series:
                tmpdata = self.apply_queued_transformations(data)
            else:
                tmpdata = data
            shape = tmpdata.shape
            dataset = nxdata.create_dataset("data",
                                            shape=(total,) + shape,
                                            dtype=numpy.float32,
                                            chunks=(1,) + shape,
                                            compression="gzip")
            dataset.attrs["interpretation"] = "image"
            dataset.attrs["signal"] = "1"
            if self.sequential_file_mode:
                for iid, imgkey in enumerate(self.sequential_file_list):
                    tmpfname = self.sequential_file_dict[imgkey]
                    img = self._open(tmpfname)
                    if img is None:
                        continue
                    self.progressBar.setValue(int((iid + 1) / total * 100.))
                    template = 'Converting and saving file %s. saving file number %d'
                    self.log.appendPlainText(template % (tmpfname, iid))
                    qt.QCoreApplication.processEvents()
                    if self.transform_data_series:
                        tmpdata = self.apply_queued_transformations(img.data)
                    else:
                        tmpdata = img.data
                    dataset[iid] = tmpdata
            else:
                for iid, data in enumerate(self.data_series):
                    self.log.appendPlainText('Saving file number %d' % iid)
                    self.progressBar.setValue(int((iid + 1) / total * 100.))
                    qt.QCoreApplication.processEvents()
                    if self.transform_data_series:
                        tmpdata = self.apply_queued_transformations(data)
                    else:
                        tmpdata = data
                    dataset[iid] = tmpdata
        self.statusBar().clear()
        self.progressBar.setValue(0)
        self.log.appendPlainText('Hdf5 Recording: Complete')

    def add_extention_if_absent(self, fname, format_):
        posslash = fname.rfind("/")
        posdot = fname.rfind(".")
        if posdot > posslash:
            return fname
        else:
            return fname + format_[1:]

    def convert_and_write(self, fname, format_, data, header):
        if format_ == '*.bin':
            with open(fname, mode="wb") as out:
                data.tofile(out)
            return
        elif format_ == '*.marccd':
            out = fabio.marccdimage.marccdimage(data=data, header=header)
        elif format_ == '*.edf':
            out = fabio.edfimage.edfimage(data=data, header=header)
        elif format_ == '*.tiff':
            out = fabio.tifimage.tifimage(data=data, header=header)
        elif format_ == '*.cbf':
            out = fabio.cbfimage.cbfimage(data=data, header=header)
        elif format_ in ['*.mar3450', '*.mar2300']:
            data = self.padd_mar(data, format_)
            out = fabio.mar345image.mar345image(data=data, header=header)
        elif format_ == '*.img':
            out = fabio.OXDimage.OXDimage(data=data, header=header)
        elif format_ == '*.sfrm':
            out = fabio.brukerimage.brukerimage(data=data, header=header)
        else:
            raise Warning("Unknown format: %s" % format_)
        template = 'Writing file %s to %s format, please wait...'
        self.statusBar().showMessage(template % (fname, format_[2:]))
        self.log.appendPlainText('Writing file %s to %s format' % (fname, format_[2:]))
        qt.QCoreApplication.processEvents()
        out.write(fname)
        self.statusBar().clearMessage()

    def convert_and_write_multiple_files(self, fname, format_):

        if self.sequential_file_mode:
            total = len(self.sequential_file_list)
            ii = 0
            for imgkey in self.sequential_file_list:
                tmpfname = self.sequential_file_dict[imgkey]
                img = self._open(tmpfname)
                if img is None:
                    continue
                self.progressBar.setValue(int((ii + 1) / total * 100.))
                self.log.appendPlainText('Converting file %s' % tmpfname)
                qt.QCoreApplication.processEvents()
                if self.transform_data_series:
                    tmpdata = self.apply_queued_transformations(img.data)
                else:
                    tmpdata = img.data
                filename = ('%s_%s%s' % (fname, self.counter_format, format_[1:])) % ii
                self.convert_and_write(filename, format_, tmpdata, img.header)
                ii += 1
        else:
            total = len(self.data_series)
            for i in range(len(self.data_series)):
                tmpdata = self.data_series[i]
                tmpheader = self.header_series[i]
                tmpfname = ('%s_%s%s' % (fname, self.counter_format, format_[1:])) % i
                self.progressBar.setValue(int((i + 1) / total * 100.))
                self.log.appendPlainText('Converting file %s' % i)
                qt.QCoreApplication.processEvents()
                if self.transform_data_series:
                    tmpdata = self.apply_queued_transformations(tmpdata)
                self.convert_and_write(tmpfname, format_, tmpdata, tmpheader)
        self.progressBar.setValue(0)
        self.log.appendPlainText('Convertion to %s: Complete' % format_[2:])

    def extract_format_from_string(self, format_long):
        for fmt in output_format:
            if fmt in format_long:
                return fmt
        raise Warning("Unknown format: %s" % format_long)

    def horizontal_mirror(self):
        if self.transform_data_series:
            if self.sequential_file_mode:
                self.transformation_queue.addItem('horizontal_mirror')
                self.transform_list += ['horizontal_mirror']
                self.log.appendPlainText('Add horizontal mirror to transformations queue')
                qt.QCoreApplication.processEvents()
            else:
                total = len(self.data_series)
                if not total:
                    message = "Could not transform image if no data have been loaded"
                    qt.QMessageBox.warning(self, 'Warning', message)
                    return
                for i in range(len(self.data_series)):
                    self.data_series[i] = numpy.flipud(self.data_series[i])[:]
                    self.progressBar.setValue(int((i + 1) / total * 100.))
                    self.log.appendPlainText('Applying horizontal mirror to data series: image %d' % i)
                    qt.QCoreApplication.processEvents()
                iid = self.imgDict[str(self.images_list.currentText())]
                self.select_new_image(None, imgID=iid)
        else:

            if self.data.any():
                self.data = numpy.flipud(self.data)[:]
                iid = self.imgDict[str(self.images_list.currentText())]
                self.data_series[iid] = self.data[:]
                self.log.appendPlainText('Applying horizontal mirror to current data')
                self.on_draw()
            else:
                message = "Could not transform image if no data have been loaded"
                qt.QMessageBox.warning(self, 'Warning', message)
        self.progressBar.setValue(0)

    def vertical_mirror(self):
        if self.transform_data_series:
            if self.sequential_file_mode:
                self.transformation_queue.addItem('vertical_mirror')
                self.transform_list += ['vertical_mirror']
                self.log.appendPlainText('Add vertical mirror to transformations queue')
                qt.QCoreApplication.processEvents()
            else:
                total = len(self.data_series)
                if not total:
                    message = "Could not transform image if no data have been loaded"
                    qt.QMessageBox.warning(self, 'Warning', message)
                    return
                for i in range(len(self.data_series)):
                    self.data_series[i] = numpy.fliplr(self.data_series[i])[:]
                    self.progressBar.setValue(int((i + 1) / total * 100.))
                    self.log.appendPlainText('Applying vertical mirror to data series: image %d' % i)
                    qt.QCoreApplication.processEvents()
                iid = self.imgDict[str(self.images_list.currentText())]
                self.select_new_image(None, imgID=iid)
        else:
            if self.data.any():
                self.data = numpy.fliplr(self.data)[:]
                iid = self.imgDict[str(self.images_list.currentText())]
                self.data_series[iid] = self.data[:]
                self.log.appendPlainText('Applying vertical mirror to current data')
                self.on_draw()
            else:
                message = "Could not transform image if no data have been loaded"
                qt.QMessageBox.warning(self, 'Warning', message)
        self.progressBar.setValue(0)

    def transposition(self):
        if self.transform_data_series:
            if self.sequential_file_mode:
                self.transformation_queue.addItem('transposition')
                self.transform_list += ['transposition']
                self.log.appendPlainText('Add transposition to transformations queue')
                qt.QCoreApplication.processEvents()
            else:
                total = len(self.data_series)
                if not total:
                    message = "Could not transform image if no data have been loaded"
                    qt.QMessageBox.warning(self, 'Warning', message)
                    return
                for i in range(len(self.data_series)):
                    self.data_series[i] = self.data_series[i].transpose()[:]
                    self.progressBar.setValue(int((i + 1) / total * 100.))
                    self.log.appendPlainText('Applying transposition to data series: image %d' % i)
                    qt.QCoreApplication.processEvents()
                iid = self.imgDict[str(self.images_list.currentText())]
                self.select_new_image(None, imgID=iid)
        else:
            if self.data.any():
                self.data = self.data.transpose()[:]
                iid = self.imgDict[str(self.images_list.currentText())]
                self.data_series[iid] = self.data[:]
                self.log.appendPlainText('Applying transposition to current data')
                self.on_draw()
            else:
                message = "Could not transform image if no data have been loaded"
                qt.QMessageBox.warning(self, 'Warning', message)
        self.progressBar.setValue(0)

    def rotation_90(self):
        if self.transform_data_series:
            if self.sequential_file_mode:
                self.transformation_queue.addItem('rotation(+90)')
                self.transform_list += ['rotation(+90)']
                self.log.appendPlainText('Add + 90 rotation to transformations queue')
                qt.QCoreApplication.processEvents()
            else:
                total = len(self.data_series)
                if not total:
                    message = "Could not transform image if no data have been loaded"
                    qt.QMessageBox.warning(self, 'Warning', message)
                    return
                for i in range(len(self.data_series)):
                    self.data_series[i] = numpy.rot90(self.data_series[i])[:]
                    self.progressBar.setValue(int((i + 1) / total * 100.))
                    self.log.appendPlainText('Applying + 90 rotation to data series: image %d' % i)
                    qt.QCoreApplication.processEvents()
                iid = self.imgDict[str(self.images_list.currentText())]
                self.select_new_image(None, imgID=iid)
        else:
            if self.data.any():
                self.data = numpy.rot90(self.data)[:]
                iid = self.imgDict[str(self.images_list.currentText())]
                self.data_series[iid] = self.data[:]
                self.log.appendPlainText('Applying + 90 rotation to current data')
                self.on_draw()
            else:
                message = "Could not transform image if no data have been loaded"
                qt.QMessageBox.warning(self, 'Warning', message)
        self.progressBar.setValue(0)

    def rotation_180(self):
        if self.transform_data_series:
            if self.sequential_file_mode:
                self.transformation_queue.addItem('rotation(+180)')
                self.transform_list += ['rotation(+180)']
                self.log.appendPlainText('Add + 180 rotation to transformations queue')
                qt.QCoreApplication.processEvents()
            else:
                total = len(self.data_series)
                if not total:
                    message = "Could not transform image if no data have been loaded"
                    qt.QMessageBox.warning(self, 'Warning', message)
                    return
                for i in range(len(self.data_series)):
                    self.data_series[i] = numpy.rot90(self.data_series[i], 2)[:]
                    self.progressBar.setValue(int((i + 1) / total * 100.))
                    self.log.appendPlainText('Applying + 180 rotation to data series: image %d' % i)
                    qt.QCoreApplication.processEvents()
                iid = self.imgDict[str(self.images_list.currentText())]
                self.select_new_image(None, imgID=iid)
        else:
            if self.data.any():
                self.data = numpy.rot90(self.data, 2)[:]
                iid = self.imgDict[str(self.images_list.currentText())]
                self.data_series[iid] = self.data[:]
                self.log.appendPlainText('Applying + 180 rotation to current data')
                self.on_draw()
            else:
                message = "Could not transform image if no data have been loaded"
                qt.QMessageBox.warning(self, 'Warning', message)
        self.progressBar.setValue(0)

    def rotation_270(self):
        if self.transform_data_series:
            if self.sequential_file_mode:
                self.transformation_queue.addItem('rotation(-90)')
                self.transform_list += ['rotation(-90)']
                self.log.appendPlainText('Add - 90 rotation to transformations queue')
                qt.QCoreApplication.processEvents()
            else:
                total = len(self.data_series)
                if not total:
                    message = "Could not transform image if no data have been loaded"
                    qt.QMessageBox.warning(self, 'Warning', message)
                    return
                for i in range(len(self.data_series)):
                    self.data_series[i] = numpy.rot90(self.data_series[i], 3)[:]
                    self.progressBar.setValue(int((i + 1) / total * 100.))
                    self.log.appendPlainText('Applying - 90 rotation to data series: image %d' % i)
                    qt.QCoreApplication.processEvents()
                iid = self.imgDict[str(self.images_list.currentText())]
                self.select_new_image(None, imgID=iid)
        else:
            if self.data.any():
                self.data = numpy.rot90(self.data, 3)[:]
                iid = self.imgDict[str(self.images_list.currentText())]
                self.data_series[iid] = self.data[:]
                self.log.appendPlainText('Applying - 90 rotation to current data')
                self.on_draw()
            else:
                message = "Could not transform image if no data have been loaded"
                qt.QMessageBox.warning(self, 'Warning', message)
        self.progressBar.setValue(0)

    def mask(self):
        message = 'Select and import a boolean mask from binary data block file'
        fname = qt.QFileDialog.getOpenFileName(self, message)
        if isinstance(fname, tuple):
            # PyQt5 compatibility
            fname = fname[0]

        fname = str(fname)
        if fname:
            dial = BinDialog(self)
            dim1, dim2, offset, bytecode, endian = dial.exec_()
            if dim1 is not None and dim2 is not None:
                if endian == 'Short':
                    endian = '<'
                else:
                    endian = '>'
                img = fabio.binaryimage.binaryimage()
                img.read(fname, dim1, dim2, offset, bytecode, endian)
                self.mask = img.data[:]
                if self.transform_data_series:
                    if self.sequential_file_mode:
                        self.transformation_queue.addItem('masking')
                        self.transform_list += ['masking']
                        self.log.appendPlainText('Add masking to transformations queue')
                        qt.QCoreApplication.processEvents()
                    else:
                        total = len(self.data_series)
                        if not total:
                            message = "Could not transform image if no data have been loaded"
                            qt.QMessageBox.warning(self, 'Warning', message)
                            return
                        for i in range(len(self.data_series)):
                            if self.data_series[i].shape != self.mask.shape:
                                message = "Mask and image have different shapes, skipping image %d" % i
                                qt.QMessageBox.warning(self, 'Warning', message)
                                self.log.appendPlainText(message)
                            else:
                                self.data_series[i] = self.mask * self.data_series[i]
                                self.progressBar.setValue(int((i + 1) / total * 100.))
                                self.log.appendPlainText('Applying mask to data series: image %d' % i)
                                qt.QCoreApplication.processEvents()
                        iid = self.imgDict[str(self.images_list.currentText())]
                        self.select_new_image(None, imgID=iid)
                else:
                    if self.data.any():
                        self.data = self.mask * self.data
                        iid = self.imgDict[str(self.images_list.currentText())]
                        self.data_series[iid] = self.data[:]
                        self.on_draw()
                        message = 'Binary boolean mask loaded and applied'
                        self.statusBar().showMessage(message, 2000)
                        self.log.appendPlainText(message)
                        qt.QCoreApplication.processEvents()
                    else:
                        message = "Could not transform image if no data have been loaded"
                        qt.QMessageBox.warning(self, 'Warning', message)
            else:
                return
        self.progressBar.setValue(0)

    def apply_queued_transformations(self, data):
        transformations = ['horizontal_mirror', 'vertical_mirror', 'transposition',
                           'rotation(+90)', 'rotation(+180)', 'rotation(-90)',
                           'masking', 'downsampling']
        for t in self.transform_list:
                if t in transformations:
                    if t == 'horizontal_mirror':
                        data = numpy.flipud(data)[:]
                        self.log.appendPlainText('horizontal_mirror Done')
                    elif t == 'vertical_mirror':
                        data = numpy.fliplr(data)[:]
                        self.log.appendPlainText('vertical_mirror Done')
                    elif t == 'transposition':
                        data = data.transpose()[:]
                        self.log.appendPlainText('transposition Done')
                    elif t == 'rotation(+90)':
                        data = numpy.rot90(data)[:]
                        self.log.appendPlainText('rotation(+90) Done')
                    elif t == 'rotation(+180)':
                        data = numpy.rot90(data, 2)[:]
                        self.log.appendPlainText('rotation(+180) Done')
                    elif t == 'rotation(-90)':
                        data = numpy.rot90(data, 3)[:]
                        self.log.appendPlainText('rotation(-90) Done')
                    elif t == 'masking':
                        data = self.mask * data
                        self.log.appendPlainText('masking Done')
                else:
                    raise Warning('Unknown transformation %s' % t)
        return data

    def transformation_options(self):
        if self.transform_option_action.isChecked():
            self.transform_data_series = True
        else:
            self.transform_data_series = False

    def clear_transform_list(self):
        self.transform_list = []
        self.transformation_queue.clear()

    def downsample(self):
        dial = DownSamplingDialog()
        thick, start_angle, step_angle = dial.exec_()
        if thick is not None:
            info = self._getSaveFileNameAndFilter(self,
                                                  "Save downsampled data series as multiple files",
                                                  qt.QDir.currentPath(),
                                                  filter=self.tr(self.defaultSaveFilter))
            if self.data_series or self.sequential_file_list:
                if str(info[0]) != '' and str(info[1]) != '':
                    format_ = self.extract_format_from_string(str(info[1]))
                    fname = self.os.path.splitext(str(info[0]))[0]

                    if self.sequential_file_mode:
                        total = len(self.sequential_file_list)
                        img = fabio.open(self.sequential_file_dict[self.sequential_file_list[0]])
                        stack = numpy.zeros_like(img.data)
                        t0 = time.time()
                        subtotal = (total // thick) * thick
                        for i in range(subtotal):
                            j = i % thick
                            k = i // thick
                            imgkey = self.sequential_file_list[i]
                            tmpfname = self.sequential_file_dict[imgkey]
                            img = self._open(tmpfname)
                            if img is None:
                                continue
                            if img.data.shape != stack.shape:
                                message = "Error image shape: %s summed data shape: %s" % (img.data.shape, stack.shape)
                                self.log.appendPlainText(message)
                                continue
                            numpy.add(stack, img.data, stack)
                            self.progressBar.setValue(int((i + 1) / subtotal * 100.))
                            self.log.appendPlainText('File %s stacked' % imgkey)
                            qt.QCoreApplication.processEvents()
                            if j == thick - 1:
                                self.log.appendPlainText('stack number %d summing up' % k)
                                qt.QCoreApplication.processEvents()
                                if format_ in ['*.mar3450', '*.mar2300']:
                                    img.header["PHI_START"] = '%.3f' % (start_angle + step_angle * (i - thick + 1))
                                    img.header["PHI_END"] = '%.3f' % (start_angle + step_angle * (i))
                                filename = ('%s_%s%s' % (fname, self.counter_format, format_[1:])) % k
                                self.convert_and_write(filename, format_, stack, img.header)
                                t1 = time.time()
                                print('time: %s' % (t1 - t0))
                                stack = numpy.zeros_like(img.data)
                                t0 = time.time()
                    else:
                        total = len(self.data_series)
                        stack = numpy.zeros_like(self.data_series[0])
                        subtotal = (total // thick) * thick
                        for i in range(subtotal):
                            j = i % thick
                            k = i // thick
                            data = self.data_series[i]
                            if data.shape != stack.shape:
                                message = "Error image shape: %s summed data shape: %s" % (img.data.shape, stack.shape)
                                self.log.appendPlainText(message)
                                continue
                            numpy.add(stack, data, stack)
                            self.progressBar.setValue(int((i + 1) / subtotal * 100.))
                            self.log.appendPlainText('File number %d stacked' % i)
                            qt.QCoreApplication.processEvents()
                            if j == thick - 1:
                                self.log.appendPlainText('stack number %d summing up' % k)
                                qt.QCoreApplication.processEvents()
                                if format_ in ['*.mar3450', '*.mar2300']:
                                    self.header_series[i]["PHI_START"] = '%.3f' % (start_angle + step_angle * (i - thick + 1))
                                    self.header_series[i]["PHI_END"] = '%.3f' % (start_angle + step_angle * (i))
                                filename = ('%s_%s%s' % (fname, self.counter_format, format_[1:])) % k
                                self.convert_and_write(filename, format_, stack, self.header_series[i])
                                stack = numpy.zeros_like(data)
                    self.progressBar.setValue(0)
                    self.log.appendPlainText('Downsampling: Complete')
                    qt.QCoreApplication.processEvents()
            else:
                if str(info[0]) != '' and str(info[1]) != '':
                    message = "Could not save image as file if no data have been loaded"
                    qt.QMessageBox.warning(self, 'Warning', message)

    def select_new_image(self, name, imgID=None):
        if imgID is not None:
            iid = imgID
        else:
            iid = self.imgDict[str(name)]
        self.data = self.data_series[iid]
        self.header = self.header_series[iid]

        self.headerTextEdit.setPlainText(str(self.format_header(self.header)))
        self.on_draw()

    def on_pick(self, event):
        if event.inaxes and self.data.any():
            x = int(round(event.xdata))
            y = int(round(event.ydata))
            if x < self.data.shape[1] and y < self.data.shape[0]:
                i = self.data[y, x]
                self.pix_coords_label.setText("Pixel coordinates and intensity: x =%6d, y =%6d, i =%6g" % (x, y, i))
            else:
                self.pix_coords_label.setText("Pixel coordinates and intensity: x = None , y = None , i = None ")
        else:
            self.pix_coords_label.setText("Pixel coordinates and intensity: x = None , y = None , i = None ")

    def on_draw(self):
        """ Redraws the figure"""
        self.statusBar().showMessage('Loading display...')
        qt.QCoreApplication.processEvents()
        # clear the axes and redraw a new plot
        self.axes.clear()
        # self.axes.imshow(numpy.log(numpy.clip(self.data,1.0e-12,1.0e260) ),interpolation = 'nearest')
        self.axes.imshow(numpy.log(self.data), interpolation='nearest')

        self.axes.set_visible(True)
        if self.axes.get_ylim()[0] < self.axes.get_ylim()[1]:
            self.axes.set_ylim(self.axes.get_ylim()[::-1])
        self.canvas.draw()
        self.statusBar().clearMessage()

    def batch_to_view(self):
        items = self.imagelistWidget.selectedItems()
        iid = 0
        item = items[0]
        item = str(item.text())
        hdfxtens = ['.h5', '.H5', '.hdf', '.HDF', 'hdf5', '.HDF5']
        for xtens in hdfxtens:
            if xtens in item:
                qt.QMessageBox.warning(self, 'Message', "Can't display hdf archive from batch mode ")
                return
        if self.sequential_file_mode:
            self.data_series = []
            self.header_series = []
            self.imgDict = {}
            self.images_list.clear()
            self.headerTextEdit.clear()
            self.axes.clear()
            self.canvas.draw()
            self.statusBar().showMessage('Import image %s in the View Mode tab, please wait...' % item)
            self.log.appendPlainText('Import image %s in the View Mode tab' % item)
            qt.QCoreApplication.processEvents()
            fname = self.sequential_file_dict[item]
            extract_fname = os.path.splitext(os.path.basename(fname))[0]
            img = self._open(fname)
            if img is None:
                return

            if img.nframes > 1:
                for img_idx in range(img.nframes):
                    frame = img.getframe(img_idx)
                    self.data_series.append(frame.data[:])
                    self.header_series.append(frame.header.copy())
                    frame_name = "%s # %i" % (extract_fname, img_idx)
                    self.images_list.addItem(frame_name)
                    self.imagelistWidget.addItem(frame_name)
                    self.imgDict[frame_name] = iid
                    self.sequential_file_list += [frame_name]
                    self.sequential_file_dict[frame_name] = fname
                    iid += 1
            else:
                self.data_series.append(img.data[:])
                self.header_series.append(img.header.copy())
                extract_fname = self.extract_fname_from_path(fname)
                self.images_list.addItem(extract_fname)
                self.imagelistWidget.addItem(extract_fname)
                self.imgDict[extract_fname] = iid
                self.sequential_file_list += [extract_fname]
                self.sequential_file_dict[extract_fname] = fname
                iid += 1

        self.statusBar().clearMessage()
        if self.data_series:
            self.select_new_image(None, imgID=0)
        self.tabWidget.setCurrentIndex(0)

    def set_counter_format_option(self):
        dial = CounterFormatOptionDialog(self.counter_format)
        self.counter_format = dial.exec_()

    def padd_mar(self, data, format_):
        dim1, dim2 = data.shape

        if format_ == '*.mar2300':
            size = 2300
        else:
            size = 3450

        left = (size - dim1) // 2
        right = size - (dim1 + left)
        up = (size - dim2) // 2
        down = size - (dim2 + up)

        out = numpy.zeros((size, size))

        if left > 0:  # pad
            outlm = left
            inlm = 0
        else:  # crop
            outlm = 0
            inlm = -left
        if right > 0:  # pad
            outrm = -right
            inrm = dim1
        else:  # crop
            outrm = size
            inrm = right
        if up > 0:  # pad
            outum = up
            inum = 0
        else:  # crop
            outum = 0
            inum = -up
        if down > 0:  # pad
            outdm = -down
            indm = dim2
        else:  # crop
            outdm = size
            indm = down

        out[outlm:outrm, outum:outdm] = data[inlm:inrm, inum:indm]
        return out

    def sequential_option(self, state):
        if not self.h5_loaded:
            if state == qt.Qt.Checked:
                self.sequential_file_mode = True
            else:
                self.sequential_file_mode = False
        else:
            self.filecheckBox.stateChanged.disconnect()
            self.filecheckBox.setCheckState(False)
            self.sequential_file_mode = False
            self.filecheckBox.stateChanged.connect(self.sequential_option)
            message = 'Sequential file mode is not compatible with hdf5 input file: option removed'
            qt.QMessageBox.warning(self, 'Message', message)

    def create_main_frame(self):

        self.tabWidget = qt.QTabWidget()
        tab1 = qt.QWidget()
        self.tabWidget.addTab(tab1, "View Mode")
        tab2 = qt.QWidget()
        self.tabWidget.addTab(tab2, "Batch Mode")

        # Tab 1

        # Create the mpl Figure and FigCanvas objects.
        # 100 dots-per-inch
        self.dpi = 100
        # self.fig = Figure((100, 100), dpi=self.dpi)
        self.fig = Figure(dpi=self.dpi)
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.canvas.setParent(tab1)

        # Since we have only one plot, we can use add_axes
        # instead of add_subplot, but then the subplot
        # configuration tool in the navigation toolbar wouldn't
        # work.
        #
        self.axes = self.fig.add_subplot(111)
        self.axes.set_visible(False)
        # Bind the 'pick' event for clicking on one of the bars
        self.canvas.mpl_connect('motion_notify_event', self.on_pick)

        # Create the navigation toolbar, tied to the canvas
        self.mpl_toolbar = NavigationToolbar2QT(self.canvas, tab1, coordinates=False)

        # Other GUI controls
        selector_label = qt.QLabel('Active Image:')
        self.images_list = qt.QComboBox(self)
        self.images_list.activated[str].connect(self.select_new_image)

        viewer_label = qt.QLabel("Images Viewer: ", self)
        self.pix_coords_label = qt.QLabel("Pixel coordinates and intensity: x = None , y = None , i = None ", self)
        self.mpl_toolbar.addWidget(self.pix_coords_label)

        self.headerTextEdit = qt.QPlainTextEdit(tab1)
        self.headerTextEdit.setReadOnly(True)
        # Layout with box sizers

        header_vbox = qt.QVBoxLayout()
        header_label = qt.QLabel("Header Info:", self)
        header_vbox.addWidget(header_label)
        header_vbox.addWidget(self.headerTextEdit)

        hbox = qt.QHBoxLayout()
        hbox.addWidget(selector_label, alignment=qt.Qt.AlignRight)
        hbox.addWidget(self.images_list)

        vbox = qt.QVBoxLayout()
        vbox.addWidget(viewer_label, alignment=qt.Qt.AlignVCenter)
        vbox.addWidget(self.canvas, alignment=qt.Qt.AlignVCenter)
        vbox.addWidget(self.mpl_toolbar, alignment=qt.Qt.AlignVCenter)
        vbox.addLayout(hbox)

        left = qt.QWidget()
        right = qt.QWidget()

        left.setLayout(header_vbox)
        right.setLayout(vbox)
        splitter = qt.QSplitter(qt.Qt.Horizontal)
        splitter.addWidget(left)
        splitter.addWidget(right)
        Bighbox = qt.QHBoxLayout()
        Bighbox.addWidget(splitter)

        tab1.setLayout(Bighbox)

        # Tab 2

        imagelistvbox = qt.QVBoxLayout()

        imagelistlabel = qt.QLabel(tab2)
        imagelistlabel.setText("Images List:")
        self.imagelistWidget = qt.QListWidget(tab2)
        import_view_button = qt.QPushButton('Export image to View Mode', tab2)
        import_view_button.clicked.connect(self.batch_to_view)

        imagelistvbox.addWidget(imagelistlabel)
        imagelistvbox.addWidget(self.imagelistWidget)
        imagelistvbox.addWidget(import_view_button)

        rightsidevbox = qt.QVBoxLayout()

        optiongroupBox = qt.QGroupBox(tab2)
        optiongroupBox.setTitle("File Modes:")

        optionbox = qt.QVBoxLayout()

        self.butttonGroup = qt.QButtonGroup()

        self.filecheckBox = qt.QCheckBox()
        self.filecheckBox.setText("Sequential access (for large data series)")
        self.filecheckBox.stateChanged.connect(self.sequential_option)
        self.butttonGroup.addButton(self.filecheckBox)

        self.filecheckBox2 = qt.QCheckBox()
        self.filecheckBox2.setText("Direct access (all images are store in memory simultaneously)")
        self.filecheckBox2.setChecked(True)
        self.butttonGroup.addButton(self.filecheckBox2)

        self.butttonGroup.setExclusive(True)

        optionbox.addWidget(self.filecheckBox)
        optionbox.addWidget(self.filecheckBox2)

        optiongroupBox.setLayout(optionbox)

        rightsidevbox.addWidget(optiongroupBox)

        splitter3 = qt.QSplitter(qt.Qt.Vertical)

        queuegroupBox = qt.QGroupBox(tab2)
        queuegroupBox.setTitle("Transformations Queue:")

        queuebox = qt.QVBoxLayout()
        self.transformation_queue = qt.QListWidget(tab2)
        queuebox.addWidget(self.transformation_queue)
        clear_trans_list_button = qt.QPushButton('Clear Transformation List', tab2)
        clear_trans_list_button.clicked.connect(self.clear_transform_list)
        queuebox.addWidget(clear_trans_list_button)

        queuegroupBox.setLayout(queuebox)

        splitter3.addWidget(queuegroupBox)

        loggroupBox = qt.QGroupBox(tab2)
        loggroupBox.setTitle("Log View:")

        logbox = qt.QHBoxLayout()
        self.log = qt.QPlainTextEdit()
        logbox.addWidget(self.log)

        loggroupBox.setLayout(logbox)
        splitter3.addWidget(loggroupBox)
        splitter3.setStretchFactor(1, 1)

        rightsidevbox.addWidget(splitter3)

        self.progressBar = qt.QProgressBar(tab2)
        self.progressBar.setProperty("value", 0)
        rightsidevbox.addWidget(self.progressBar)

        left2 = qt.QWidget()
        right2 = qt.QWidget()
        left2.setLayout(imagelistvbox)
        right2.setLayout(rightsidevbox)
        splitter2 = qt.QSplitter(qt.Qt.Horizontal)
        splitter2.addWidget(left2)
        splitter2.addWidget(right2)
        splitter2.setStretchFactor(1, 2)

        Bighbox2 = qt.QHBoxLayout()
        Bighbox2.addWidget(splitter2)

        tab2.setLayout(Bighbox2)

        self.setCentralWidget(self.tabWidget)

    def create_status_bar(self):
        self.status_text = qt.QLabel('')
        self.statusBar().addWidget(self.status_text, 1)
        self.statusBar().showMessage('Thanks for using FabIO viewer.', 5000)

    def on_about(self):
        msg = [__doc__,
               "",
               "Version: \t\t%s" % __version__,
               "FabIO version: \t%s" % fabio.version,
               "Author: \t\t%s" % __author__,
               "Copyright: \t\t%s" % __copyright__,
               "License: \t\t%s" % __licence__]

        qt.QMessageBox.about(self, "About FabIO Viewer", os.linesep.join(msg))

    def create_menu(self):
        self.file_menu = self.menuBar().addMenu("&File")
        self.open_menu = self.file_menu.addMenu("&Open")

        action = self.create_action("&Image(s)",
                                    shortcut="",
                                    slot=self.open_data_series,
                                    tip="Load single file and data series (files sequence)")
        self.add_actions(self.open_menu, (action,))

        action = self.create_action("&Hdf5 data series",
                                    shortcut="",
                                    slot=self.open_h5_data_series,
                                    tip="Load single file and data series (files sequence)")
        self.add_actions(self.open_menu, (action,))

        self.save_as_menu = self.file_menu.addMenu("&Save")

        action = self.create_action("&Active image",
                                    slot=self.save_as,
                                    shortcut="",
                                    tip="Save/Convert the image which is currently displayed")
        self.add_actions(self.save_as_menu, (action,))

        self.save_data_series_menu = self.save_as_menu.addMenu("&Data series as")

        action = self.create_action("&Multiple files",
                                    slot=self.save_data_series_as_multiple_file,
                                    shortcut="",
                                    tip="Save/Convert the set of images currently loaded into the images list")
        self.add_actions(self.save_data_series_menu, (action,))

        action = self.create_action("&Hdf5 archive",
                                    slot=self.save_data_series_as_singlehdf,
                                    shortcut="",
                                    tip="Save/Convert the set of images currently loaded into the images list")
        self.add_actions(self.save_data_series_menu, (action,))

        action = self.create_action("&Quit",
                                    slot=self.close,
                                    shortcut="Ctrl+Q",
                                    tip="Close the application")
        self.add_actions(self.file_menu, (action,))

        self.transform_menu = self.menuBar().addMenu("&Transform")
        self.mirror_menu = self.transform_menu.addMenu("&Mirror")

        action = self.create_action("&Horizontal",
                                    shortcut='',
                                    slot=self.horizontal_mirror,
                                    tip="Horizontal mirror")
        self.add_actions(self.mirror_menu, (action,))

        action = self.create_action("&Vertical",
                                    shortcut='',
                                    slot=self.vertical_mirror,
                                    tip="Vertical mirror")
        self.add_actions(self.mirror_menu, (action,))

        action = self.create_action("&Transposition",
                                    shortcut='',
                                    slot=self.transposition,
                                    tip="Transposition")
        self.add_actions(self.mirror_menu, (action,))

        self.rotation_menu = self.transform_menu.addMenu("&Rotation")

        action = self.create_action("+90",
                                    shortcut='',
                                    slot=self.rotation_90,
                                    tip="Rotation of +90 degrees (counter-clockwise)")
        self.add_actions(self.rotation_menu, (action,))

        action = self.create_action("+180",
                                    shortcut='',
                                    slot=self.rotation_180,
                                    tip="Rotation of +180 degrees (counter-clockwise)")
        self.add_actions(self.rotation_menu, (action,))

        action = self.create_action("- 90",
                                    shortcut='',
                                    slot=self.rotation_270,
                                    tip="Rotation of -90 degrees (counter-clockwise)")
        self.add_actions(self.rotation_menu, (action,))

        action = self.create_action("&Mask",
                                    shortcut='',
                                    slot=self.mask,
                                    tip="Import a mask from file and apply it to image(s)")
        self.add_actions(self.transform_menu, (action,))

        action = self.create_action("&Downsample",
                                    shortcut='',
                                    slot=self.downsample,
                                    tip="Summation over groups of images")
        self.add_actions(self.transform_menu, (action,))

        tip = "Define if transformations are applied to the whole data series (checked)"\
            " or only to the active image (unchecked) "
        action = self.create_action("&Apply transform to the whole data series",
                                    shortcut='',
                                    slot=self.transformation_options,
                                    tip=tip)
        action.setCheckable(True)
        self.add_actions(self.transform_menu, (action,))
        self.transform_option_action = action

        self.options = self.menuBar().addMenu("&Options")

        action = self.create_action("&Counter format",
                                    shortcut='',
                                    slot=self.set_counter_format_option,
                                    tip='Allow to define the format for the counter in multiple saving')
        self.add_actions(self.options, (action,))

        self.help_menu = self.menuBar().addMenu("&Help")

        action = self.create_action("&About",
                                    shortcut='F1',
                                    slot=self.on_about,
                                    tip='About Images Converter')
        self.add_actions(self.help_menu, (action,))

    def add_actions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def create_action(self, text, slot=None, shortcut=None, icon=None, tip=None, checkable=False, signal="triggered"):
        action = qt.QAction(text, self)
        if icon is not None:
            action.setIcon(qt.QIcon(":/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            getattr(action, signal).connect(slot)

        if checkable:
            action.setCheckable(True)
        return action


class CounterFormatOptionDialog(qt.QDialog):  # option doivent refleter l etat des couche du dessous
    """Dialog containing entry for down sampling"""

    def __init__(self, counter_format, parent=None):
        qt.QDialog.__init__(self, parent)
        self.resize(350, 100)
        self.setWindowTitle('Options')
        self.counter_format = counter_format
        buttonBox = qt.QDialogButtonBox(self)
        buttonBox.setGeometry(qt.QRect(0, 60, 341, 32))
        buttonBox.setOrientation(qt.Qt.Horizontal)
        buttonBox.setStandardButtons(qt.QDialogButtonBox.Cancel | qt.QDialogButtonBox.Ok)

        label = qt.QLabel(self)
        label.setGeometry(qt.QRect(38, 23, 181, 16))
        label.setText("File Counter format:")

        self.lineEdit = qt.QLineEdit(self)
        self.lineEdit.setGeometry(qt.QRect(175, 18, 113, 25))
        self.lineEdit.setText(counter_format)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

    def exec_(self):
        if qt.QDialog.exec_(self) == qt.QDialog.Accepted:
            if str(self.lineEdit.text()) != '':
                return str(self.lineEdit.text())
            else:
                message = "All informations are mandatory, please fill the blanks"
                qt.QMessageBox.warning(self, 'Warning', message)
        else:
            return self.counter_format


class DownSamplingDialog(qt.QDialog):
    """Dialog containing entry for down sampling"""

    def __init__(self, parent=None):
        qt.QDialog.__init__(self, parent)
        self.resize(407, 250)
        self.setWindowTitle('Downsampling')
        buttonBox = qt.QDialogButtonBox(self)
        buttonBox.setGeometry(qt.QRect(45, 200, 341, 32))
        buttonBox.setOrientation(qt.Qt.Horizontal)
        buttonBox.setStandardButtons(qt.QDialogButtonBox.Cancel | qt.QDialogButtonBox.Ok)

        label = qt.QLabel(self)
        label.setGeometry(qt.QRect(38, 63, 181, 16))
        label.setText("Number of files to sum up:")

        self.lineEdit = qt.QLineEdit(self)
        self.lineEdit.setGeometry(qt.QRect(220, 58, 113, 25))

        label2 = qt.QLabel(self)
        label2.setGeometry(qt.QRect(90, 100, 131, 20))
        label2.setText("Starting Phi angle:")

        self.lineEdit2 = qt.QLineEdit(self)
        self.lineEdit2.setGeometry(qt.QRect(220, 95, 113, 25))

        label3 = qt.QLabel(self)
        label3.setGeometry(qt.QRect(151, 133, 101, 16))
        label3.setText("Phi step:")

        self.lineEdit3 = qt.QLineEdit(self)
        self.lineEdit3.setGeometry(qt.QRect(219, 130, 113, 25))

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

    def exec_(self):
        if qt.QDialog.exec_(self) == qt.QDialog.Accepted:
            if str(self.lineEdit.text()) != '' and str(self.lineEdit2.text()) != '' and str(self.lineEdit3.text()) != '':
                return int(str(self.lineEdit.text())), float(str(self.lineEdit2.text())), float(str(self.lineEdit3.text()))
            else:
                message = "All informations are mandatory, please fill the blanks"
                qt.QMessageBox.warning(self, 'Warning', message)
        else:
            return None, None, None


class BinDialog(qt.QDialog):
    """Dialog containing entry for binary data block opening"""

    def __init__(self, parent=None):
        qt.QDialog.__init__(self, parent)
        self.resize(410, 270)
        self.setWindowTitle("Binary data block opening")

        self.dim1 = None
        self.dim2 = None
        self.offset = None
        self.bytecode = None
        self.endian = None

        buttonBox = qt.QDialogButtonBox(self)
        buttonBox.setGeometry(qt.QRect(50, 230, 341, 32))
        buttonBox.setOrientation(qt.Qt.Horizontal)
        buttonBox.setStandardButtons(qt.QDialogButtonBox.Cancel | qt.QDialogButtonBox.Ok)

        groupBox = qt.QGroupBox(self)
        groupBox.setGeometry(qt.QRect(10, 10, 370, 191))
        groupBox.setTitle("Binary data block required informations:")
        label = qt.QLabel(self)
        label.setGeometry(qt.QRect(67, 48, 91, 16))
        label.setText("Dimention 1:")
        label_2 = qt.QLabel(self)
        label_2.setGeometry(qt.QRect(66, 76, 91, 16))
        label_2.setText("Dimention 2:")
        self.lineEdit = qt.QLineEdit(self)
        self.lineEdit.setGeometry(qt.QRect(185, 40, 91, 25))
        self.lineEdit_2 = qt.QLineEdit(self)
        self.lineEdit_2.setGeometry(qt.QRect(185, 70, 91, 25))
        label_5 = qt.QLabel(self)
        label_5.setGeometry(qt.QRect(105, 106, 51, 16))
        label_5.setText("Offset:")
        self.lineEdit_3 = qt.QLineEdit(self)
        self.lineEdit_3.setGeometry(qt.QRect(184, 100, 91, 25))
        self.lineEdit_3.setText('0')
        label_3 = qt.QLabel(groupBox)
        label_3.setGeometry(qt.QRect(70, 130, 91, 16))
        label_3.setText("ByteCode:")
        self.comboBox = qt.QComboBox(groupBox)
        self.comboBox.setGeometry(qt.QRect(173, 123, 91, 25))
        bytecodes = ["int8", "int16", "int32", "int64",
                     "uint8", "uint16", "uint32", "uint64",
                     "float32", "float64"]
        for bytecode in bytecodes:
            self.comboBox.addItem(bytecode)
        self.comboBox.setCurrentIndex(2)
        label_4 = qt.QLabel(self)
        label_4.setGeometry(qt.QRect(98, 170, 61, 16))
        label_4.setText("Endian:")
        self.comboBox_2 = qt.QComboBox(self)
        self.comboBox_2.setGeometry(qt.QRect(182, 166, 91, 25))
        self.comboBox_2.addItem("Short")
        self.comboBox_2.addItem("Long")

        buttonBox.rejected.connect(self.cancel)
        buttonBox.accepted.connect(self.binary_block_info)

    def binary_block_info(self):
        if str(self.lineEdit.text()) != '' and str(self.lineEdit_2.text()) != '' and str(self.lineEdit_3.text()) != '':
            self.dim1 = int(str(self.lineEdit.text()))
            self.dim2 = int(str(self.lineEdit_2.text()))
            self.offset = int(str(self.lineEdit_3.text()))
        else:
            message = "All informations are mandatory, please fill the blanks"
            qt.QMessageBox.warning(self, 'Warning', message)
            return
        self.bytecode = str(self.comboBox.currentText())
        self.endian = str(self.comboBox_2.currentText())
        self.accept()

    def cancel(self):
        self.close()

    def exec_(self):
        if qt.QDialog.exec_(self) == qt.QDialog.Accepted:
            return self.dim1, self.dim2, self.offset, self.bytecode, self.endian
        else:
            return None, None, None, None, None


def main():
    parser = ArgumentParser(prog="fabio_viewer", usage="fabio_viewer img1 img2... imgn",
                            description=__doc__,
                            epilog="Based on FabIO version %s" % fabio.version)
    parser.add_argument("images", nargs="*")
    parser.add_argument("-V", "--version", action='version', version=__version__, help="Print version & quit")
    args = parser.parse_args()
    qt.QApplication.setStyle(qt.QStyleFactory.create("Cleanlooks"))
    app = qt.QApplication([])
    form = AppForm()
    if args.images:
        form.open_data_series(args.images)
    form.show()
    return app.exec_()


if __name__ == "__main__":
    result = main()
    sys.exit(result)
