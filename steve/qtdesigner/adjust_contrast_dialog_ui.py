# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'adjust_contrast_dialog.ui'
#
# Created: Thu Jun 04 08:51:06 2015
#      by: PyQt4 UI code generator 4.9.6
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(340, 116)
        self.gridLayout = QtGui.QGridLayout(Dialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.high_spin_box = QtGui.QSpinBox(Dialog)
        self.high_spin_box.setObjectName(_fromUtf8("high_spin_box"))
        self.gridLayout.addWidget(self.high_spin_box, 1, 2, 1, 1)
        self.high_contrast_slider = QtGui.QSlider(Dialog)
        self.high_contrast_slider.setOrientation(QtCore.Qt.Horizontal)
        self.high_contrast_slider.setObjectName(_fromUtf8("high_contrast_slider"))
        self.gridLayout.addWidget(self.high_contrast_slider, 1, 1, 1, 1)
        self.low_spin_box = QtGui.QSpinBox(Dialog)
        self.low_spin_box.setObjectName(_fromUtf8("low_spin_box"))
        self.gridLayout.addWidget(self.low_spin_box, 2, 0, 1, 1)
        self.low_contrast_slider = QtGui.QSlider(Dialog)
        self.low_contrast_slider.setOrientation(QtCore.Qt.Horizontal)
        self.low_contrast_slider.setObjectName(_fromUtf8("low_contrast_slider"))
        self.gridLayout.addWidget(self.low_contrast_slider, 2, 1, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 3, 1, 1, 1)
        self.high_contrast_label = QtGui.QLabel(Dialog)
        self.high_contrast_label.setObjectName(_fromUtf8("high_contrast_label"))
        self.gridLayout.addWidget(self.high_contrast_label, 1, 0, 1, 1)
        self.low_contrast_label = QtGui.QLabel(Dialog)
        self.low_contrast_label.setObjectName(_fromUtf8("low_contrast_label"))
        self.gridLayout.addWidget(self.low_contrast_label, 2, 2, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), Dialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Dialog", None))
        self.high_contrast_label.setText(_translate("Dialog", "High", None))
        self.low_contrast_label.setText(_translate("Dialog", "Low", None))

