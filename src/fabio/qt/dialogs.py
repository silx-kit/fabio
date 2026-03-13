#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Project: Fast Azimuthal integration
#             https://github.com/silx-kit/pyFAI
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
#  furnished to do so, subject to the following conditions.
#  .
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#  .
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
Portable diffraction images viewer/converter
* Written in Python, it combines the functionalities of the I/O library fabIO
  with a user-friendly Qt GUI.
* Image converter is also a light viewer based on the visualization tool
  provided by the module matplotlib.
"""

# ----------------------------------------------------------------------
# Imports (QtPy, FabIO, NumPy, Matplotlib, …)
# ----------------------------------------------------------------------
import numpy
from qtpy import QtWidgets as qt
from qtpy.QtWidgets import (
    QMessageBox,
    QLabel,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
)

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


# ──────────────────────────────────────────────────────────────────────
#   Dialog windows – now fully English
# ──────────────────────────────────────────────────────────────────────
class CounterFormatOptionDialog(QDialog):
    """Dialog that lets the user set the file‑counter format used when saving
    a series of files."""

    def __init__(self, counter_format, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Counter format")
        self.resize(350, 100)
        # ----- layout ----------------------------------------------------
        button_box = QDialogButtonBox(self)
        button_box.setGeometry(qt.QRect(0, 60, 341, 32))
        button_box.setOrientation(qt.Qt.Horizontal)
        button_box.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        label = QLabel("File counter format:", self)
        label.setGeometry(qt.QRect(38, 23, 181, 16))
        self.lineEdit = qt.QLineEdit(self)
        self.lineEdit.setGeometry(qt.QRect(175, 18, 113, 25))
        self.lineEdit.setText(counter_format)
        # ----- signals ---------------------------------------------------
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def exec_(self):
        """Return the new format string if the user clicks *Ok*,
        otherwise return the original value."""
        if super().exec_() == QDialog.Accepted:
            new_text = str(self.lineEdit.text()).strip()
            if new_text:
                return new_text
            QMessageBox.warning(
                self,
                "Warning",
                "The counter format cannot be empty – the previous value will be kept.",
            )
        return self.lineEdit.text()


class DownSamplingDialog(QDialog):
    """Dialog that gathers the parameters required for down‑sampling
    (summation) of a stack of images."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Down‑sampling")
        self.resize(410, 250)
        # ----- layout ----------------------------------------------------
        button_box = QDialogButtonBox(self)
        button_box.setGeometry(qt.QRect(45, 200, 341, 32))
        button_box.setOrientation(qt.Qt.Horizontal)
        button_box.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        # Number of files to sum
        label_n = QLabel("Number of files to sum:", self)
        label_n.setGeometry(qt.QRect(38, 63, 181, 16))
        self.lineEdit_n = qt.QLineEdit(self)
        self.lineEdit_n.setGeometry(qt.QRect(220, 58, 113, 25))
        # Starting phi angle
        label_phi0 = QLabel("Starting φ angle (degrees):", self)
        label_phi0.setGeometry(qt.QRect(90, 100, 191, 20))
        self.lineEdit_phi0 = qt.QLineEdit(self)
        self.lineEdit_phi0.setGeometry(qt.QRect(300, 95, 113, 25))
        # Phi step
        label_step = QLabel("φ step (degrees):", self)
        label_step.setGeometry(qt.QRect(151, 133, 101, 16))
        self.lineEdit_step = qt.QLineEdit(self)
        self.lineEdit_step.setGeometry(qt.QRect(260, 130, 113, 25))
        # ----- signals ---------------------------------------------------
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def exec_(self):
        """Return a tuple *(thick, start_angle, step_angle)* if the user
        confirms, otherwise *(None, None, None)*."""
        if super().exec_() == QDialog.Accepted:
            if (
                self.lineEdit_n.text()
                and self.lineEdit_phi0.text()
                and self.lineEdit_step.text()
            ):
                try:
                    thick = int(self.lineEdit_n.text())
                    start_angle = float(self.lineEdit_phi0.text())
                    step_angle = float(self.lineEdit_step.text())
                except ValueError:
                    QMessageBox.warning(
                        self,
                        "Invalid input",
                        "Please enter numeric values for all fields.",
                    )
                    return None, None, None
                return thick, start_angle, step_angle
            QMessageBox.warning(
                self,
                "Missing data",
                "All fields are mandatory – please fill them before confirming.",
            )
        return None, None, None


class BinDialog(QDialog):
    """Dialog that asks the user for the parameters needed to read a raw
    binary data block (dimensions, offset, byte‑code, endian)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Binary data block opening")
        self.resize(410, 270)
        # ----- internal state --------------------------------------------
        self.dim1 = None
        self.dim2 = None
        self.offset = None
        self.bytecode = None
        self.endian = None
        # ----- layout ----------------------------------------------------
        button_box = QDialogButtonBox(self)
        button_box.setGeometry(qt.QRect(50, 230, 341, 32))
        button_box.setOrientation(qt.Qt.Horizontal)
        button_box.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        group_box = QGroupBox("Binary data block required information:", self)
        group_box.setGeometry(qt.QRect(10, 10, 370, 191))
        # Dimension 1
        label_dim1 = QLabel("Dimension 1:", group_box)
        label_dim1.setGeometry(qt.QRect(67, 48, 91, 16))
        self.lineEdit_dim1 = qt.QLineEdit(group_box)
        self.lineEdit_dim1.setGeometry(qt.QRect(185, 40, 91, 25))
        # Dimension 2
        label_dim2 = QLabel("Dimension 2:", group_box)
        label_dim2.setGeometry(qt.QRect(66, 76, 91, 16))
        self.lineEdit_dim2 = qt.QLineEdit(group_box)
        self.lineEdit_dim2.setGeometry(qt.QRect(185, 70, 91, 25))
        # Offset
        label_offset = QLabel("Offset:", group_box)
        label_offset.setGeometry(qt.QRect(105, 106, 51, 16))
        self.lineEdit_offset = qt.QLineEdit(group_box)
        self.lineEdit_offset.setGeometry(qt.QRect(184, 100, 91, 25))
        self.lineEdit_offset.setText("0")
        # Byte code
        label_bc = QLabel("Byte code:", group_box)
        label_bc.setGeometry(qt.QRect(70, 130, 91, 16))
        self.comboBox_bc = qt.QComboBox(group_box)
        self.comboBox_bc.setGeometry(qt.QRect(173, 123, 91, 25))
        for bc in [
            "int8",
            "int16",
            "int32",
            "int64",
            "uint8",
            "uint16",
            "uint32",
            "uint64",
            "float32",
            "float64",
        ]:
            self.comboBox_bc.addItem(bc)
        self.comboBox_bc.setCurrentIndex(2)  # default to int32
        # Endian
        label_endian = QLabel("Endian:", group_box)
        label_endian.setGeometry(qt.QRect(98, 170, 61, 16))
        self.comboBox_endian = qt.QComboBox(group_box)
        self.comboBox_endian.setGeometry(qt.QRect(182, 166, 91, 25))
        self.comboBox_endian.addItem("Little‑endian")
        self.comboBox_endian.addItem("Big‑endian")
        # ----- signals ---------------------------------------------------
        button_box.accepted.connect(self._accept)
        button_box.rejected.connect(self.reject)

    # ------------------------------------------------------------------
    def _accept(self):
        """Validate the entries and store them before closing the dialog."""
        if (
            self.lineEdit_dim1.text()
            and self.lineEdit_dim2.text()
            and self.lineEdit_offset.text()
        ):
            try:
                self.dim1 = int(self.lineEdit_dim1.text())
                self.dim2 = int(self.lineEdit_dim2.text())
                self.offset = int(self.lineEdit_offset.text())
            except ValueError:
                QMessageBox.warning(
                    self,
                    "Invalid input",
                    "Dimensions and offset must be integer numbers.",
                )
                return
        else:
            QMessageBox.warning(
                self,
                "Missing data",
                "All fields are mandatory – please fill them before confirming.",
            )
            return
        self.bytecode = str(self.comboBox_bc.currentText())
        # QtPy returns the displayed text, which we map back to the original
        # “Short” / “Long” terminology used later in the code.
        self.endian = (
            "Short" if self.comboBox_endian.currentText() == "Little‑endian" else "Long"
        )
        self.accept()

    # ------------------------------------------------------------------
    def exec_(self):
        """Return the 5‑tuple *(dim1, dim2, offset, bytecode, endian)*
        if the user clicks **Ok**, otherwise a tuple of ``None``."""
        if super().exec_() == QDialog.Accepted:
            return (
                self.dim1,
                self.dim2,
                self.offset,
                self.bytecode,
                self.endian,
            )
        return None, None, None, None, None
