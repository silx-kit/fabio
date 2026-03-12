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

__version__ = "1.1"
__author__ = "Gaël Goret, Jérôme Kieffer"
__copyright__ = "2015-2026 ESRF"
__licence__ = "MIT"

import os
import numpy
import fabio
from fabio.nexus import Nexus
# ----------------------------------------------------------------------
# Qt imports via QtPy – this works with PyQt5, PySide2, PySide6, etc.
# ----------------------------------------------------------------------
from qtpy import QtWidgets as qt
from qtpy import QtCore as qtc
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import (
    QSizePolicy,
    QFileDialog,
    QMessageBox,
    QAction,
    QComboBox,
    QPlainTextEdit,
    QLabel,
    QSplitter,
    QTabWidget,
    QWidget,
    QProgressBar,
    QGroupBox,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QListWidget,
    QCheckBox,
    QButtonGroup
)
# Matplotlib imports (unchanged)
from matplotlib.figure import Figure
from .matplotlib import FigureCanvasQTAgg
from .matplotlib import NavigationToolbar2QT
from .dialogs import CounterFormatOptionDialog, DownSamplingDialog, BinDialog
# ----------------------------------------------------------------------
# Global configuration
# ----------------------------------------------------------------------
numpy.seterr(divide="ignore")

output_format = [
    "*.bin",
    "*.cbf",
    "*.edf",
    "*.h5",
    "*.img",
    "*.mar2300",
    "*.mar3450",
    "*.marccd",
    "*.tiff",
    "*.sfrm",
]
# ----------------------------------------------------------------------
# Main application class
# ----------------------------------------------------------------------
class AppForm(qt.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        # ------------------------------------------------------------------
        # Window set‑up
        # ------------------------------------------------------------------
        self.setWindowTitle("FabIO Viewer")
        self.setSizePolicy(
            QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        )
        # Menu / widgets
        self.create_menu()
        self.create_main_frame()
        self.create_status_bar()
        # ------------------------------------------------------------------
        # Data containers
        # ------------------------------------------------------------------
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
        self.counter_format = "%03d"
    # ----------------------------------------------------------------------
    # Helper methods
    # ----------------------------------------------------------------------
    def format_header(self, d):
        """Return a nicely formatted header string.

        :param d: dict containing headers
        :return: formated string
	"""
        keys = sorted(d.keys())
        return " \n".join([f"{k}: {d[k]}" for k in keys]) + " \n"

    def _open(self, filename):
        """Open an image with fabio, falling back to manual binary import."""
        try:
            img = fabio.open(filename)
        except Exception:
            message = (
                "Automatic format recognition procedure failed or perhaps you are "
                "trying to open a binary data block...\n\nSwitch to manual procedure."
            )
            QMessageBox.warning(self, "Message", message)
            dim1, dim2, offset, bytecode, endian = BinDialog(self).exec_()
            if dim1 is not None and dim2 is not None:
                endian = "<" if endian == "Short" else ">"
                img = fabio.binaryimage.binaryimage()
                img.read(filename, dim1, dim2, offset, bytecode, endian)
                img.header = {
                    "Info": "No header information available in binary data blocks"
                }
            else:
                return None
        return img
    # ----------------------------------------------------------------------
    # File‑opening / series handling
    # ----------------------------------------------------------------------
    def open_data_series(self, series=None):
        if not series:
            series = QFileDialog.getOpenFileNames(
                self, "Select and open series of files"
            )
            if isinstance(series, tuple):
                # PyQt5 compatibility – QtPy returns a tuple as well
                series = series[0]
        series = [str(f) for f in list(series)]
        total = len(series)
        if total == 0:
            return
        # Reset UI / internal state
        self.data_series = []
        self.header_series = []
        self.sequential_file_list = []
        self.imgDict = {}
        self.sequential_file_dict = {}
        self.images_list.clear()
        self.imagelistWidget.clear()
        self.headerTextEdit.clear()
        self.axes.clear()
        self.canvas.draw()
        self.h5_loaded = False
        iid = 0
        for fname in series:
            if not fname:
                continue
            extract_fname = self.extract_fname_from_path(fname)
            if self.sequential_file_mode:
                self.statusBar().showMessage(
                    f"Adding path {fname} to batch image list, please wait..."
                )
                self.log.appendPlainText(
                    f"Adding path {fname} to batch image list"
                )
                qtc.QCoreApplication.processEvents()
                self.imagelistWidget.addItem(extract_fname)
                self.sequential_file_list.append(extract_fname)
                self.sequential_file_dict[extract_fname] = fname
                iid += 1
            else:
                self.statusBar().showMessage(
                    f"Opening file {fname}, please wait..."
                )
                self.log.appendPlainText(f"Opening file {fname}")
                qtc.QCoreApplication.processEvents()
                img = self._open(fname)
                if img is None:
                    continue
                if img.nframes > 1:
                    for img_idx in range(img.nframes):
                        frame = img.getframe(img_idx)
                        self.data_series.append(frame.data[:])
                        self.header_series.append(frame.header.copy())
                        frame_name = f"{extract_fname} # {img_idx}"
                        self.images_list.addItem(frame_name)
                        self.imagelistWidget.addItem(frame_name)
                        self.imgDict[frame_name] = iid
                        self.sequential_file_list.append(frame_name)
                        self.sequential_file_dict[frame_name] = fname
                        iid += 1
                else:
                    self.data_series.append(img.data[:])
                    self.header_series.append(img.header.copy())
                    self.images_list.addItem(extract_fname)
                    self.imagelistWidget.addItem(extract_fname)
                    self.imgDict[extract_fname] = iid
                    self.sequential_file_list.append(extract_fname)
                    self.sequential_file_dict[extract_fname] = fname
                    iid += 1
            self.progressBar.setValue(int((iid + 1) / total * 100.0))
        self.statusBar().clearMessage()
        self.progressBar.setValue(0)
        self.log.appendPlainText("Opening procedure: Complete")
        if self.data_series:
            self.select_new_image(None, imgID=0)
    def open_h5_data_series(self):
        fname = QFileDialog.getOpenFileName(self, "Select and open series of files")
        if isinstance(fname, tuple):
            fname = fname[0]
        fname = str(fname)
        if not fname:
            return
        self.h5_loaded = True
        if self.filecheckBox.checkState():
            self.filecheckBox.stateChanged.disconnect()
            self.filecheckBox.setCheckState(qtc.Qt.Unchecked)
            self.sequential_file_mode = False
            self.filecheckBox.stateChanged.connect(self.sequential_option)
            QMessageBox.warning(
                self,
                "Message",
                "Sequential file mode is not compatible with hdf5 input file: option removed",
            )
        # Reset UI / state
        self.data_series = []
        self.header_series = []
        self.sequential_file_list = []
        self.sequential_file_dict = {}
        self.imagelistWidget.clear()
        self.headerTextEdit.clear()
        with Nexus(fname, "r") as nxs:
            entry = nxs.get_entries()[0]
            nxdata = nxs.get_class(entry, class_type="NXdata")[0]
            dataset = nxdata.get("data", numpy.zeros(shape=(1, 1, 1)))
            total = dataset.shape[0]
            imgDict = {}
            base_name = os.path.basename(os.path.splitext(fname)[0])
            self.images_list.clear()
            safeiid = 0
            for iid in range(total):
                self.progressBar.setValue(int((iid + 1) / total * 100.0))
                self.log.appendPlainText(
                    f"Extracting data from hdf5 archive, image number {iid}"
                )
                qtc.QCoreApplication.processEvents()
                self.data_series.append(dataset[iid])
                self.header_series.append(
                    {"Info": "No header information available in hdf5 Archive"}
                )
                imgDict[f"{base_name}{iid}"] = safeiid
                self.images_list.addItem(f"{base_name}{iid}")
                safeiid += 1
        self.statusBar().clearMessage()
        self.progressBar.setValue(0)
        self.log.appendPlainText("Hdf5 Extraction: Complete")
        self.imgDict = imgDict.copy()
        if self.data_series:
            self.select_new_image(None, imgID=0)
    # ----------------------------------------------------------------------
    # UI helpers
    # ----------------------------------------------------------------------
    def extract_fname_from_path(self, name):
        pos = name.rfind("/")
        return name[pos + 1 :] if pos > -1 else name
    # ----------------------------------------------------------------------
    # Save dialogs & conversion utilities
    # ----------------------------------------------------------------------
    defaultSaveFilter = (
        "binary data block (*.bin);;"
        "cbf image (*.cbf);;"
        "edf image (*.edf);;"
        "oxford diffraction image (*.img);;"
        "mar2300 image(*.mar2300);;"
        "mar3450 image (*.mar3450);;"
        "marccd image (*.marccd));;"
        "tiff image (*.tiff);;"
        "bruker image (*.sfrm)"
    )

    def _getSaveFileNameAndFilter(self, parent=None, caption="", directory="", filter=""):
        dialog = QFileDialog(parent, caption=caption, directory=directory)
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setNameFilter(filter)
        if not dialog.exec_():
            return "", ""
        return dialog.selectedFiles()[0], dialog.selectedNameFilter()

    def save_as(self):
        info = self._getSaveFileNameAndFilter(
            self,
            "Save active image as",
            qt.QDir.currentPath(),
            filter=self.tr(self.defaultSaveFilter),
        )
        if self.data.any():
            if info[0] and info[1]:
                fmt = self.extract_format_from_string(str(info[1]))
                fname = self.add_extention_if_absent(str(info[0]), fmt)
                self.convert_and_write(fname, fmt, self.data, self.header)
        else:
            if info[0] and info[1]:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "Could not save image as file if no data have been loaded",
                )
    def save_data_series_as_multiple_file(self):
        info = self._getSaveFileNameAndFilter(
            self,
            "Save data series as multiple files",
            qt.QDir.currentPath(),
            filter=self.tr(self.defaultSaveFilter),
        )
        if self.data_series or self.sequential_file_list:
            if info[0] and info[1]:
                fmt = self.extract_format_from_string(str(info[1]))
                fname = os.path.splitext(str(info[0]))[0]
                self.convert_and_write_multiple_files(fname, fmt)
        else:
            if info[0] and info[1]:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "Could not save image as file if no data have been loaded",
                )
    def save_data_series_as_singlehdf(self):
        info = self._getSaveFileNameAndFilter(
            self,
            "Save data series as single high density file",
            qt.QDir.currentPath(),
            filter=self.tr("HDF5 archive (*.h5)"),
        )
        if self.data_series or self.sequential_file_list:
            if info[0] and info[1]:
                fmt = self.extract_format_from_string(str(info[1]))
                fname = self.add_extention_if_absent(str(info[0]), fmt)
                if fmt == "*.h5":
                    self.convert_and_save_to_h5(fname)
                else:
                    QMessageBox.warning(self, "Warning", f"Unknown format: {fmt}")
        else:
            if info[0] and info[1]:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "Could not save image as file if no data have been loaded",
                )
    # ----------------------------------------------------------------------
    # Conversion / I/O core
    # ----------------------------------------------------------------------
    def convert_and_save_to_h5(self, fname):
        """Save a stack as a Nexus entry (creates a new entry for each image)."""
        with Nexus(fname) as nxs:
            entry = nxs.new_entry(
                entry="entry", program_name="fabio_viewer", title="FabIO Viewer"
            )
            nxdata = nxs.new_class(entry, "fabio", class_type="NXdata")
            # Determine shape & total number of images
            if self.sequential_file_mode:
                total = len(self.sequential_file_list)
                first_fname = self.sequential_file_dict[self.sequential_file_list[0]]
                img = self._open(first_fname)
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
            dataset = nxdata.create_dataset(
                "data",
                shape=(total,) + shape,
                dtype=numpy.float32,
                chunks=(1,) + shape,
                compression="gzip",
            )
            dataset.attrs["interpretation"] = "image"
            dataset.attrs["signal"] = "1"
            if self.sequential_file_mode:
                for iid, imgkey in enumerate(self.sequential_file_list):
                    tmpfname = self.sequential_file_dict[imgkey]
                    img = self._open(tmpfname)
                    if img is None:
                        continue
                    self.progressBar.setValue(int((iid + 1) / total * 100.0))
                    self.log.appendPlainText(
                        f"Converting and saving file {tmpfname}. saving file number {iid}"
                    )
                    qtc.QCoreApplication.processEvents()
                    if self.transform_data_series:
                        tmpdata = self.apply_queued_transformations(img.data)
                    else:
                        tmpdata = img.data
                    dataset[iid] = tmpdata
            else:
                for iid, data in enumerate(self.data_series):
                    self.log.appendPlainText(f"Saving file number {iid}")
                    self.progressBar.setValue(int((iid + 1) / total * 100.0))
                    qtc.QCoreApplication.processEvents()
                    if self.transform_data_series:
                        tmpdata = self.apply_queued_transformations(data)
                    else:
                        tmpdata = data
                    dataset[iid] = tmpdata
        self.statusBar().clear()
        self.progressBar.setValue(0)
        self.log.appendPlainText("Hdf5 Recording: Complete")
    def add_extention_if_absent(self, fname, fmt):
        """Append the required extension if the filename does not already have one."""
        slash = fname.rfind("/")
        dot = fname.rfind(".")
        return fname if dot > slash else fname + fmt[1:]
    def convert_and_write(self, fname, fmt, data, header):
        """Write a single image in the requested format."""
        if fmt == "*.bin":
            with open(fname, mode="wb") as out:
                data.tofile(out)
            return
        elif fmt == "*.marccd":
            out = fabio.marccdimage.marccdimage(data=data, header=header)
        elif fmt == "*.edf":
            out = fabio.edfimage.edfimage(data=data, header=header)
        elif fmt == "*.tiff":
            out = fabio.tifimage.tifimage(data=data, header=header)
        elif fmt == "*.cbf":
            out = fabio.cbfimage.cbfimage(data=data, header=header)
        elif fmt in ("*.mar3450", "*.mar2300"):
            data = self.padd_mar(data, fmt)
            out = fabio.mar345image.mar345image(data=data, header=header)
        elif fmt == "*.img":
            out = fabio.OXDimage.OXDimage(data=data, header=header)
        elif fmt == "*.sfrm":
            out = fabio.brukerimage.brukerimage(data=data, header=header)
        else:
            raise Warning(f"Unknown format: {fmt}")
        self.statusBar().showMessage(
            f"Writing file {fname} to {fmt[2:]} format, please wait..."
        )
        self.log.appendPlainText(f"Writing file {fname} to {fmt[2:]} format")
        qtc.QCoreApplication.processEvents()
        out.write(fname)
        self.statusBar().clearMessage()

    def convert_and_write_multiple_files(self, fname, fmt):
        """Write a series of images to separate files."""
        if self.sequential_file_mode:
            total = len(self.sequential_file_list)
            ii = 0
            for imgkey in self.sequential_file_list:
                tmpfname = self.sequential_file_dict[imgkey]
                img = self._open(tmpfname)
                if img is None:
                    continue
                self.progressBar.setValue(int((ii + 1) / total * 100.0))
                self.log.appendPlainText(f"Converting file {tmpfname}")
                qtc.QCoreApplication.processEvents()
                if self.transform_data_series:
                    tmpdata = self.apply_queued_transformations(img.data)
                else:
                    tmpdata = img.data
                outname = (f"{fname}_{self.counter_format}{fmt[1:]}") % ii
                self.convert_and_write(outname, fmt, tmpdata, img.header)
                ii += 1
        else:
            total = len(self.data_series)
            for i in range(total):
                tmpdata = self.data_series[i]
                tmpheader = self.header_series[i]
                outname = (f"{fname}_{self.counter_format}{fmt[1:]}") % i
                self.progressBar.setValue(int((i + 1) / total * 100.0))
                self.log.appendPlainText(f"Converting file {i}")
                qtc.QCoreApplication.processEvents()
                if self.transform_data_series:
                    tmpdata = self.apply_queued_transformations(tmpdata)
                self.convert_and_write(outname, fmt, tmpdata, tmpheader)
        self.progressBar.setValue(0)
        self.log.appendPlainText(f"Convertion to {fmt[2:]}: Complete")
    def extract_format_from_string(self, fmt_long):
        for fmt in output_format:
            if fmt in fmt_long:
                return fmt
        raise Warning(f"Unknown format: {fmt_long}")
    # ----------------------------------------------------------------------
    # Image transformations
    # ----------------------------------------------------------------------
    def horizontal_mirror(self):
        if self.transform_data_series:
            if self.sequential_file_mode:
                self.transformation_queue.addItem("horizontal_mirror")
                self.transform_list.append("horizontal_mirror")
                self.log.appendPlainText(
                    "Add horizontal mirror to transformations queue"
                )
                qtc.QCoreApplication.processEvents()
            else:
                total = len(self.data_series)
                if not total:
                    QMessageBox.warning(
                        self,
                        "Warning",
                        "Could not transform image if no data have been loaded",
                    )
                    return
                for i in range(total):
                    self.data_series[i] = numpy.flipud(self.data_series[i])[:]
                    self.progressBar.setValue(int((i + 1) / total * 100.0))
                    self.log.appendPlainText(
                        f"Applying horizontal mirror to data series: image {i}"
                    )
                    qtc.QCoreApplication.processEvents()
                iid = self.imgDict[str(self.images_list.currentText())]
                self.select_new_image(None, imgID=iid)
        else:
            if self.data.any():
                self.data = numpy.flipud(self.data)[:]
                iid = self.imgDict[str(self.images_list.currentText())]
                self.data_series[iid] = self.data[:]
                self.log.appendPlainText("Applying horizontal mirror to current data")
                self.on_draw()
            else:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "Could not transform image if no data have been loaded",
                )
        self.progressBar.setValue(0)

    def vertical_mirror(self):
        if self.transform_data_series:
            if self.sequential_file_mode:
                self.transformation_queue.addItem("vertical_mirror")
                self.transform_list.append("vertical_mirror")
                self.log.appendPlainText(
                    "Add vertical mirror to transformations queue"
                )
                qtc.QCoreApplication.processEvents()
            else:
                total = len(self.data_series)
                if not total:
                    QMessageBox.warning(
                        self,
                        "Warning",
                        "Could not transform image if no data have been loaded",
                    )
                    return
                for i in range(total):
                    self.data_series[i] = numpy.fliplr(self.data_series[i])[:]
                    self.progressBar.setValue(int((i + 1) / total * 100.0))
                    self.log.appendPlainText(
                        f"Applying vertical mirror to data series: image {i}"
                    )
                    qtc.QCoreApplication.processEvents()
                iid = self.imgDict[str(self.images_list.currentText())]
                self.select_new_image(None, imgID=iid)
        else:
            if self.data.any():
                self.data = numpy.fliplr(self.data)[:]
                iid = self.imgDict[str(self.images_list.currentText())]
                self.data_series[iid] = self.data[:]
                self.log.appendPlainText("Applying vertical mirror to current data")
                self.on_draw()
            else:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "Could not transform image if no data have been loaded",
                )
        self.progressBar.setValue(0)

    def transposition(self):
        if self.transform_data_series:
            if self.sequential_file_mode:
                self.transformation_queue.addItem("transposition")
                self.transform_list.append("transposition")
                self.log.appendPlainText(
                    "Add transposition to transformations queue"
                )
                qtc.QCoreApplication.processEvents()
            else:
                total = len(self.data_series)
                if not total:
                    QMessageBox.warning(
                        self,
                        "Warning",
                        "Could not transform image if no data have been loaded",
                    )
                    return
                for i in range(total):
                    self.data_series[i] = self.data_series[i].transpose()[:]
                    self.progressBar.setValue(int((i + 1) / total * 100.0))
                    self.log.appendPlainText(
                        f"Applying transposition to data series: image {i}"
                    )
                    qtc.QCoreApplication.processEvents()
                iid = self.imgDict[str(self.images_list.currentText())]
                self.select_new_image(None, imgID=iid)
        else:
            if self.data.any():
                self.data = self.data.transpose()[:]
                iid = self.imgDict[str(self.images_list.currentText())]
                self.data_series[iid] = self.data[:]
                self.log.appendPlainText("Applying transposition to current data")
                self.on_draw()
            else:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "Could not transform image if no data have been loaded",
                )
        self.progressBar.setValue(0)

    def rotation_90(self):
        if self.transform_data_series:
            if self.sequential_file_mode:
                self.transformation_queue.addItem("rotation(+90)")
                self.transform_list.append("rotation(+90)")
                self.log.appendPlainText("Add + 90 rotation to transformations queue")
                qtc.QCoreApplication.processEvents()
            else:
                total = len(self.data_series)
                if not total:
                    QMessageBox.warning(
                        self,
                        "Warning",
                        "Could not transform image if no data have been loaded",
                    )
                    return
                for i in range(total):
                    self.data_series[i] = numpy.rot90(self.data_series[i])[:]
                    self.progressBar.setValue(int((i + 1) / total * 100.0))
                    self.log.appendPlainText(
                        f"Applying + 90 rotation to data series: image {i}"
                    )
                    qtc.QCoreApplication.processEvents()
                iid = self.imgDict[str(self.images_list.currentText())]
                self.select_new_image(None, imgID=iid)
        else:
            if self.data.any():
                self.data = numpy.rot90(self.data)[:]
                iid = self.imgDict[str(self.images_list.currentText())]
                self.data_series[iid] = self.data[:]
                self.log.appendPlainText("Applying + 90 rotation to current data")
                self.on_draw()
            else:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "Could not transform image if no data have been loaded",
                )
        self.progressBar.setValue(0)

    def rotation_180(self):
        if self.transform_data_series:
            if self.sequential_file_mode:
                self.transformation_queue.addItem("rotation(+180)")
                self.transform_list.append("rotation(+180)")
                self.log.appendPlainText("Add + 180 rotation to transformations queue")
                qtc.QCoreApplication.processEvents()
            else:
                total = len(self.data_series)
                if not total:
                    QMessageBox.warning(
                        self,
                        "Warning",
                        "Could not transform image if no data have been loaded",
                    )
                    return
                for i in range(total):
                    self.data_series[i] = numpy.rot90(self.data_series[i], 2)[:]
                    self.progressBar.setValue(int((i + 1) / total * 100.0))
                    self.log.appendPlainText(
                        f"Applying + 180 rotation to data series: image {i}"
                    )
                    qtc.QCoreApplication.processEvents()
                iid = self.imgDict[str(self.images_list.currentText())]
                self.select_new_image(None, imgID=iid)
        else:
            if self.data.any():
                self.data = numpy.rot90(self.data, 2)[:]
                iid = self.imgDict[str(self.images_list.currentText())]
                self.data_series[iid] = self.data[:]
                self.log.appendPlainText("Applying + 180 rotation to current data")
                self.on_draw()
            else:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "Could not transform image if no data have been loaded",
                )
        self.progressBar.setValue(0)

    def rotation_270(self):
        if self.transform_data_series:
            if self.sequential_file_mode:
                self.transformation_queue.addItem("rotation(-90)")
                self.transform_list.append("rotation(-90)")
                self.log.appendPlainText("Add - 90 rotation to transformations queue")
                qtc.QCoreApplication.processEvents()
            else:
                total = len(self.data_series)
                if not total:
                    QMessageBox.warning(
                        self,
                        "Warning",
                        "Could not transform image if no data have been loaded",
                    )
                    return
                for i in range(total):
                    self.data_series[i] = numpy.rot90(self.data_series[i], 3)[:]
                    self.progressBar.setValue(int((i + 1) / total * 100.0))
                    self.log.appendPlainText(
                        f"Applying - 90 rotation to data series: image {i}"
                    )
                    qtc.QCoreApplication.processEvents()
                iid = self.imgDict[str(self.images_list.currentText())]
                self.select_new_image(None, imgID=iid)
        else:
            if self.data.any():
                self.data = numpy.rot90(self.data, 3)[:]
                iid = self.imgDict[str(self.images_list.currentText())]
                self.data_series[iid] = self.data[:]
                self.log.appendPlainText("Applying - 90 rotation to current data")
                self.on_draw()
            else:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "Could not transform image if no data have been loaded",
                )
        self.progressBar.setValue(0)

    def mask(self):
        fname = QFileDialog.getOpenFileName(self, "Select and import a boolean mask from binary data block file")
        if isinstance(fname, tuple):
            fname = fname[0]

        fname = str(fname)
        if not fname:
            return
        dim1, dim2, offset, bytecode, endian = BinDialog(self).exec_()
        if dim1 is None:
            return
        endian = "<" if endian == "Short" else ">"
        img = fabio.binaryimage.binaryimage()
        img.read(fname, dim1, dim2, offset, bytecode, endian)
        self.mask = img.data[:]
        if self.transform_data_series:
            if self.sequential_file_mode:
                self.transformation_queue.addItem("masking")
                self.transform_list.append("masking")
                self.log.appendPlainText("Add masking to transformations queue")
                qtc.QCoreApplication.processEvents()
            else:
                total = len(self.data_series)
                if not total:
                    QMessageBox.warning(
                        self,
                        "Warning",
                        "Could not transform image if no data have been loaded",
                    )
                    return
                for i in range(total):
                    if self.data_series[i].shape != self.mask.shape:
                        msg = f"Mask and image have different shapes, skipping image {i}"
                        QMessageBox.warning(self, "Warning", msg)
                        self.log.appendPlainText(msg)
                    else:
                        self.data_series[i] = self.mask * self.data_series[i]
                        self.progressBar.setValue(int((i + 1) / total * 100.0))
                        self.log.appendPlainText(
                            f"Applying mask to data series: image {i}"
                        )
                        qtc.QCoreApplication.processEvents()
                iid = self.imgDict[str(self.images_list.currentText())]
                self.select_new_image(None, imgID=iid)
        else:
            if self.data.any():
                self.data = self.mask * self.data
                iid = self.imgDict[str(self.images_list.currentText())]
                self.data_series[iid] = self.data[:]
                self.on_draw()
                self.statusBar().showMessage("Binary boolean mask loaded and applied", 2000)
                self.log.appendPlainText("Binary boolean mask loaded and applied")
            else:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "Could not transform image if no data have been loaded",
                )
        self.progressBar.setValue(0)
    def downsample(self):
        thick, start_angle, step_angle = DownSamplingDialog().exec_()
        if thick is None:
            return
        info = self._getSaveFileNameAndFilter(
            self,
            "Save downsampled data series as multiple files",
            qt.QDir.currentPath(),
            filter=self.tr(self.defaultSaveFilter),
        )
        if not (self.data_series or self.sequential_file_list):
            if info[0] and info[1]:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "Could not save image as file if no data have been loaded",
                )
            return
        if not (info[0] and info[1]):
            return
        fmt = self.extract_format_from_string(str(info[1]))
        fname = os.path.splitext(str(info[0]))[0]
        if self.sequential_file_mode:
            total = len(self.sequential_file_list)
            stack = None
            subtotal = (total // thick) * thick
            for i in range(subtotal):
                j = i % thick
                k = i // thick
                imgkey = self.sequential_file_list[i]
                tmpfname = self.sequential_file_dict[imgkey]
                img = self._open(tmpfname)
                if img is None:
                    continue
                if stack is None:
                    stack = numpy.zeros_like(img.data)
                if img.data.shape != stack.shape:
                    self.log.appendPlainText(
                        f"Error image shape: {img.data.shape} summed data shape: {stack.shape}"
                    )
                    continue
                numpy.add(stack, img.data, stack)
                self.progressBar.setValue(int((i + 1) / subtotal * 100.0))
                self.log.appendPlainText(f"File {imgkey} stacked")
                qtc.QCoreApplication.processEvents()
                if j == thick - 1:
                    self.log.appendPlainText(f"stack number {k} summing up")
                    qtc.QCoreApplication.processEvents()
                    if fmt in ("*.mar3450", "*.mar2300"):
                        img.header["PHI_START"] = f"{start_angle + step_angle * (i - thick + 1):.3f}"
                        img.header["PHI_END"] = f"{start_angle + step_angle * i:.3f}"
                    outname = (f"{fname}_{self.counter_format}{fmt[1:]}") % k
                    self.convert_and_write(outname, fmt, stack, img.header)
                    stack = numpy.zeros_like(img.data)
        else:
            total = len(self.data_series)
            stack = numpy.zeros_like(self.data_series[0])
            subtotal = (total // thick) * thick
            for i in range(subtotal):
                j = i % thick
                k = i // thick
                data = self.data_series[i]
                if data.shape != stack.shape:
                    self.log.appendPlainText(
                        f"Error image shape: {data.shape} summed data shape: {stack.shape}"
                    )
                    continue
                numpy.add(stack, data, stack)
                self.progressBar.setValue(int((i + 1) / subtotal * 100.0))
                self.log.appendPlainText(f"File number {i} stacked")
                qtc.QCoreApplication.processEvents()
                if j == thick - 1:
                    self.log.appendPlainText(f"stack number {k} summing up")
                    qtc.QCoreApplication.processEvents()
                    if fmt in ("*.mar3450", "*.mar2300"):
                        self.header_series[i]["PHI_START"] = f"{start_angle + step_angle * (i - thick + 1):.3f}"
                        self.header_series[i]["PHI_END"] = f"{start_angle + step_angle * i:.3f}"
                    outname = (f"{fname}_{self.counter_format}{fmt[1:]}") % k
                    self.convert_and_write(outname, fmt, stack, self.header_series[i])
                    stack = numpy.zeros_like(data)
        self.progressBar.setValue(0)
        self.log.appendPlainText("Downsampling: Complete")
        qtc.QCoreApplication.processEvents()
    # ----------------------------------------------------------------------
    # UI callbacks – image selection, drawing, etc.
    # ----------------------------------------------------------------------
    def select_new_image(self, name, imgID=None):
        iid = imgID if imgID is not None else self.imgDict[str(name)]
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
                self.pix_coords_label.setText(
                    f"Pixel coordinates and intensity: x ={x:6d}, y ={y:6d}, i ={i:6g}"
                )
            else:
                self.pix_coords_label.setText(
                    "Pixel coordinates and intensity: x = None , y = None , i = None "
                )
        else:
            self.pix_coords_label.setText(
                "Pixel coordinates and intensity: x = None , y = None , i = None "
            )

    def on_draw(self):
        """Redraws the figure"""
        self.statusBar().showMessage("Loading display...")
        qtc.QCoreApplication.processEvents()
        self.axes.clear()
        self.axes.imshow(numpy.arcsinh(self.data), interpolation="nearest")

        self.axes.set_visible(True)
        if self.axes.get_ylim()[0] < self.axes.get_ylim()[1]:
            self.axes.set_ylim(self.axes.get_ylim()[::-1])
        self.canvas.draw()
        self.statusBar().clearMessage()

    def batch_to_view(self):
        items = self.imagelistWidget.selectedItems()
        if not items:
            return
        item = str(items[0].text())
        if any(ext in item.lower() for ext in (".h5", ".hdf", ".hdf5")):
            QMessageBox.warning(
                self, "Message", "Can't display hdf archive from batch mode "
            )
            return
        if self.sequential_file_mode:
            self.data_series = []
            self.header_series = []
            self.imgDict = {}
            self.images_list.clear()
            self.headerTextEdit.clear()
            self.axes.clear()
            self.canvas.draw()
            self.statusBar().showMessage(
                f"Import image {item} in the View Mode tab, please wait..."
            )
            self.log.appendPlainText(f"Import image {item} in the View Mode tab")
            qtc.QCoreApplication.processEvents()
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
                    frame_name = f"{extract_fname} # {img_idx}"
                    self.images_list.addItem(frame_name)
                    self.imagelistWidget.addItem(frame_name)
                    self.imgDict[frame_name] = len(self.data_series) - 1
            else:
                self.data_series.append(img.data[:])
                self.header_series.append(img.header.copy())
                self.images_list.addItem(extract_fname)
                self.imagelistWidget.addItem(extract_fname)
                self.imgDict[extract_fname] = len(self.data_series) - 1
        self.statusBar().clearMessage()
        if self.data_series:
            self.select_new_image(None, imgID=0)
        self.tabWidget.setCurrentIndex(0)

    def set_counter_format_option(self):
        self.counter_format = CounterFormatOptionDialog(self.counter_format).exec_()
    def padd_mar(self, data, fmt):
        """Pad or crop MAR images to the required 2300×2300 or 3450×3450 size."""
        dim1, dim2 = data.shape
        size = 2300 if fmt == "*.mar2300" else 3450
        left = (size - dim1) // 2
        right = size - (dim1 + left)
        up = (size - dim2) // 2
        down = size - (dim2 + up)

        out = numpy.zeros((size, size))
        # Compute slice indices (positive → pad, negative → crop)
        in_lm, out_lm = (0, left) if left > 0 else (-left, 0)
        in_rm, out_rm = (dim1, size) if right > 0 else (dim1 - right, size)
        in_um, out_um = (0, up) if up > 0 else (-up, 0)
        in_dm, out_dm = (dim2, size) if down > 0 else (dim2 - down, size)
        out[out_lm:out_rm, out_um:out_dm] = data[in_lm:in_rm, in_um:in_dm]
        return out

    def sequential_option(self, state):
        if not self.h5_loaded:
            self.sequential_file_mode = state == qtc.Qt.Checked
        else:
            self.filecheckBox.stateChanged.disconnect()
            self.filecheckBox.setCheckState(qtc.Qt.Unchecked)
            self.sequential_file_mode = False
            self.filecheckBox.stateChanged.connect(self.sequential_option)
            QMessageBox.warning(
                self,
                "Message",
                "Sequential file mode is not compatible with hdf5 input file: option removed",
            )
    # ----------------------------------------------------------------------
    # Menu / toolbar creation
    # ----------------------------------------------------------------------
    def create_menu(self):
        self.file_menu = self.menuBar().addMenu("&File")
        self.open_menu = self.file_menu.addMenu("&Open")
        # ---- Open ----
        self.add_actions(
            self.open_menu,
            (
                self.create_action(
                    "&Image(s)",
                    slot=self.open_data_series,
                    tip="Load single file and data series (files sequence)",
                ),
                self.create_action(
                    "&Hdf5 data series",
                    slot=self.open_h5_data_series,
                    tip="Load a series stored in an HDF5 file",
                ),
            ),
        )
        # ---- Save ----
        self.save_as_menu = self.file_menu.addMenu("&Save")
        self.add_actions(
            self.save_as_menu,
            (
                self.create_action(
                    "&Active image",
                    slot=self.save_as,
                    tip="Save/Convert the image which is currently displayed",
                ),
            ),
        )
        self.save_data_series_menu = self.save_as_menu.addMenu("&Data series as")
        self.add_actions(
            self.save_data_series_menu,
            (
                self.create_action(
                    "&Multiple files",
                    slot=self.save_data_series_as_multiple_file,
                    tip="Save/Convert the set of images currently loaded into the images list",
                ),
                self.create_action(
                    "&Hdf5 archive",
                    slot=self.save_data_series_as_singlehdf,
                    tip="Save/Convert the set of images currently loaded into the images list",
                ),
            ),
        )
        self.add_actions(
            self.file_menu,
            (
                self.create_action(
                    "&Quit", slot=self.close, shortcut="Ctrl+Q", tip="Close the application"
                ),
            ),
        )
        # ---- Transform ----
        self.transform_menu = self.menuBar().addMenu("&Transform")
        self.mirror_menu = self.transform_menu.addMenu("&Mirror")
        self.add_actions(
            self.mirror_menu,
            (
                self.create_action(
                    "&Horizontal", slot=self.horizontal_mirror, tip="Horizontal mirror"
                ),
                self.create_action(
                    "&Vertical", slot=self.vertical_mirror, tip="Vertical mirror"
                ),
                self.create_action(
                    "&Transposition", slot=self.transposition, tip="Transposition"
                ),
            ),
        )
        self.rotation_menu = self.transform_menu.addMenu("&Rotation")
        self.add_actions(
            self.rotation_menu,
            (
                self.create_action(
                    "+90", slot=self.rotation_90, tip="Rotation of +90 degrees (counter‑clockwise)"
                ),
                self.create_action(
                    "+180", slot=self.rotation_180, tip="Rotation of +180 degrees (counter‑clockwise)"
                ),
                self.create_action(
                    "- 90", slot=self.rotation_270, tip="Rotation of -90 degrees (counter‑clockwise)"
                ),
            ),
        )
        self.add_actions(
            self.transform_menu,
            (
                self.create_action(
                    "&Mask", slot=self.mask, tip="Import a mask from file and apply it to image(s)"
                ),
                self.create_action(
                    "&Downsample",
                    slot=self.downsample,
                    tip="Summation over groups of images",
                ),
                self.create_action(
                    "&Apply transform to the whole data series",
                    slot=self.transformation_options,
                    tip=(
                        "If checked, transformations are applied to the whole data series; "
                        "if unchecked, only the active image is affected"
                    ),
                ),
            ),
        )
        self.transform_option_action = self.transform_menu.actions()[-1]
        self.transform_option_action.setCheckable(True)
        # ---- Options ----
        self.options = self.menuBar().addMenu("&Options")
        self.add_actions(
            self.options,
            (
                self.create_action(
                    "&Counter format",
                    slot=self.set_counter_format_option,
                    tip="Define the format for the counter in multiple saving",
                ),
            ),
        )
        # ---- Help ----
        self.help_menu = self.menuBar().addMenu("&Help")
        self.add_actions(
            self.help_menu,
            (
                self.create_action(
                    "&About", slot=self.on_about, shortcut="F1", tip="About FabIO Viewer"
                ),
            ),
        )
    def add_actions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)
    def create_action(
        self,
        text,
        slot=None,
        shortcut=None,
        icon=None,
        tip=None,
        checkable=False,
        signal="triggered",
    ):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            getattr(action, signal).connect(slot)
        action.setCheckable(checkable)
        return action
    # ----------------------------------------------------------------------
    # Main UI layout (tabs, canvases, log, etc.)
    # ----------------------------------------------------------------------
    def create_main_frame(self):
        self.tabWidget = QTabWidget()
        tab1 = QWidget()
        self.tabWidget.addTab(tab1, "View Mode")
        tab2 = QWidget()
        self.tabWidget.addTab(tab2, "Batch Mode")
        # ------------------------------------------------------------------
        # Matplotlib canvas (View Mode)
        # ------------------------------------------------------------------
        self.dpi = 100
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
        self.canvas.mpl_connect("motion_notify_event", self.on_pick)

        # Create the navigation toolbar, tied to the canvas
        self.mpl_toolbar = NavigationToolbar2QT(self.canvas, tab1, coordinates=False)
        # ------------------------------------------------------------------
        # Header display (left side)
        # ------------------------------------------------------------------
        header_vbox = QVBoxLayout()
        header_label = QLabel("Header Info:", self)
        header_vbox.addWidget(header_label)
        self.headerTextEdit = QPlainTextEdit(tab1)
        self.headerTextEdit.setReadOnly(True)
        header_vbox.addWidget(self.headerTextEdit)
        # ------------------------------------------------------------------
        # Image selector & viewer (right side)
        # ------------------------------------------------------------------
        selector_label = QLabel("Active Image:", self)
        self.images_list = QComboBox(self)
        self.images_list.textActivated.connect(self.select_new_image)
        viewer_label = QLabel("Images Viewer:", self)
        self.pix_coords_label = QLabel(
            "Pixel coordinates and intensity: x = None , y = None , i = None ", self
        )
        self.mpl_toolbar.addWidget(self.pix_coords_label)
        hbox = QHBoxLayout()
        hbox.addWidget(selector_label, alignment=qtc.Qt.AlignRight)
        hbox.addWidget(self.images_list)
        vbox = QVBoxLayout()
        vbox.addWidget(viewer_label, alignment=qtc.Qt.AlignVCenter)
        vbox.addWidget(self.canvas, alignment=qtc.Qt.AlignVCenter)
        vbox.addWidget(self.mpl_toolbar, alignment=qtc.Qt.AlignVCenter)
        vbox.addLayout(hbox)
        left = QWidget()
        right = QWidget()
        left.setLayout(header_vbox)
        right.setLayout(vbox)
        splitter = QSplitter(qtc.Qt.Horizontal)
        splitter.addWidget(left)
        splitter.addWidget(right)
        main_hbox = QHBoxLayout()
        main_hbox.addWidget(splitter)
        tab1.setLayout(main_hbox)
        # ------------------------------------------------------------------
        # Batch Mode UI (tab 2)
        # ------------------------------------------------------------------
        imagelistvbox = QVBoxLayout()
        imagelistlabel = QLabel("Images List:", tab2)
        self.imagelistWidget = QListWidget(tab2)
        import_view_button = QPushButton("Export image to View Mode", tab2)
        import_view_button.clicked.connect(self.batch_to_view)

        imagelistvbox.addWidget(imagelistlabel)
        imagelistvbox.addWidget(self.imagelistWidget)
        imagelistvbox.addWidget(import_view_button)
        # File‑mode options
        optiongroupBox = QGroupBox("File Modes:", tab2)
        optionbox = QVBoxLayout()
        self.butttonGroup = QButtonGroup()
        self.filecheckBox = QCheckBox("Sequential access (for large data series)", tab2)
        self.filecheckBox.stateChanged.connect(self.sequential_option)
        self.butttonGroup.addButton(self.filecheckBox)
        self.filecheckBox2 = QCheckBox(
            "Direct access (all images are stored in memory simultaneously)", tab2
        )
        self.filecheckBox2.setChecked(True)
        self.butttonGroup.addButton(self.filecheckBox2)

        self.butttonGroup.setExclusive(True)

        optionbox.addWidget(self.filecheckBox)
        optionbox.addWidget(self.filecheckBox2)

        optiongroupBox.setLayout(optionbox)
        # Transformations queue
        queuegroupBox = QGroupBox("Transformations Queue:", tab2)
        queuebox = QVBoxLayout()
        self.transformation_queue = QListWidget(tab2)
        queuebox.addWidget(self.transformation_queue)
        clear_trans_list_button = QPushButton("Clear Transformation List", tab2)
        clear_trans_list_button.clicked.connect(self.clear_transform_list)
        queuebox.addWidget(clear_trans_list_button)

        queuegroupBox.setLayout(queuebox)
        # Log view
        loggroupBox = QGroupBox("Log View:", tab2)
        logbox = QHBoxLayout()
        self.log = QPlainTextEdit()
        logbox.addWidget(self.log)

        loggroupBox.setLayout(logbox)
        # Progress bar
        self.progressBar = QProgressBar(tab2)
        self.progressBar.setProperty("value", 0)
        # Assemble right‑hand side of Batch tab
        rightsidevbox = QVBoxLayout()
        rightsidevbox.addWidget(optiongroupBox)
        rightsidevbox.addWidget(queuegroupBox)
        rightsidevbox.addWidget(loggroupBox)
        rightsidevbox.addWidget(self.progressBar)
        left2 = QWidget()
        right2 = QWidget()
        left2.setLayout(imagelistvbox)
        right2.setLayout(rightsidevbox)
        splitter2 = QSplitter(qtc.Qt.Horizontal)
        splitter2.addWidget(left2)
        splitter2.addWidget(right2)
        splitter2.setStretchFactor(1, 2)
        batch_hbox = QHBoxLayout()
        batch_hbox.addWidget(splitter2)
        tab2.setLayout(batch_hbox)
        self.setCentralWidget(self.tabWidget)

    def create_status_bar(self):
        self.status_text = QLabel("")
        self.statusBar().addWidget(self.status_text, 1)
        self.statusBar().showMessage("Thanks for using FabIO viewer.", 5000)

    def on_about(self):
        msg = [
            __doc__,
            "",
            f"Version: \t\t{__version__}",
            f"FabIO version: \t{fabio.version}",
            f"Author: \t\t{__author__}",
            f"Copyright: \t\t{__copyright__}",
            f"License: \t\t{__licence__}",
        ]
        QMessageBox.about(self, "About FabIO Viewer", os.linesep.join(msg))
    # ----------------------------------------------------------------------
    # Miscellaneous UI helpers
    # ----------------------------------------------------------------------
    def clear_transform_list(self):
        self.transform_list = []
        self.transformation_queue.clear()
    def transformation_options(self):
        self.transform_data_series = self.transform_option_action.isChecked()
