# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'adjust_contrast_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.7
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(340, 116)
        self.gridLayout = QtWidgets.QGridLayout(Dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.high_spin_box = QtWidgets.QSpinBox(Dialog)
        self.high_spin_box.setObjectName("high_spin_box")
        self.gridLayout.addWidget(self.high_spin_box, 1, 2, 1, 1)
        self.high_contrast_slider = QtWidgets.QSlider(Dialog)
        self.high_contrast_slider.setOrientation(QtCore.Qt.Horizontal)
        self.high_contrast_slider.setObjectName("high_contrast_slider")
        self.gridLayout.addWidget(self.high_contrast_slider, 1, 1, 1, 1)
        self.low_spin_box = QtWidgets.QSpinBox(Dialog)
        self.low_spin_box.setObjectName("low_spin_box")
        self.gridLayout.addWidget(self.low_spin_box, 2, 0, 1, 1)
        self.low_contrast_slider = QtWidgets.QSlider(Dialog)
        self.low_contrast_slider.setOrientation(QtCore.Qt.Horizontal)
        self.low_contrast_slider.setObjectName("low_contrast_slider")
        self.gridLayout.addWidget(self.low_contrast_slider, 2, 1, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 3, 1, 1, 1)
        self.high_contrast_label = QtWidgets.QLabel(Dialog)
        self.high_contrast_label.setObjectName("high_contrast_label")
        self.gridLayout.addWidget(self.high_contrast_label, 1, 0, 1, 1)
        self.low_contrast_label = QtWidgets.QLabel(Dialog)
        self.low_contrast_label.setObjectName("low_contrast_label")
        self.gridLayout.addWidget(self.low_contrast_label, 2, 2, 1, 1)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.high_contrast_label.setText(_translate("Dialog", "High"))
        self.low_contrast_label.setText(_translate("Dialog", "Low"))

