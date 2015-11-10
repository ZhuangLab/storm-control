# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'galvo.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
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
        Dialog.resize(360, 180)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        Dialog.setMinimumSize(QtCore.QSize(360, 180))
        Dialog.setMaximumSize(QtCore.QSize(360, 180))
        self.focusLockBox = QtGui.QGroupBox(Dialog)
        self.focusLockBox.setGeometry(QtCore.QRect(10, 0, 341, 141))
        self.focusLockBox.setObjectName(_fromUtf8("focusLockBox"))
        self.xAxisControlBox = QtGui.QGroupBox(self.focusLockBox)
        self.xAxisControlBox.setGeometry(QtCore.QRect(10, 20, 155, 105))
        self.xAxisControlBox.setObjectName(_fromUtf8("xAxisControlBox"))
        self.gridLayout = QtGui.QGridLayout(self.xAxisControlBox)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.xOffsetSpinBox = QtGui.QDoubleSpinBox(self.xAxisControlBox)
        self.xOffsetSpinBox.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.xOffsetSpinBox.setMinimum(0.0)
        self.xOffsetSpinBox.setMaximum(100.0)
        self.xOffsetSpinBox.setSingleStep(0.01)
        self.xOffsetSpinBox.setObjectName(_fromUtf8("xOffsetSpinBox"))
        self.gridLayout.addWidget(self.xOffsetSpinBox, 0, 0, 1, 1)
        self.xOffsetLabel = QtGui.QLabel(self.xAxisControlBox)
        self.xOffsetLabel.setObjectName(_fromUtf8("xOffsetLabel"))
        self.gridLayout.addWidget(self.xOffsetLabel, 0, 1, 1, 1)
        self.xAmplitudeSpinBox = QtGui.QDoubleSpinBox(self.xAxisControlBox)
        self.xAmplitudeSpinBox.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.xAmplitudeSpinBox.setMinimum(0.0)
        self.xAmplitudeSpinBox.setMaximum(100.0)
        self.xAmplitudeSpinBox.setSingleStep(0.01)
        self.xAmplitudeSpinBox.setObjectName(_fromUtf8("xAmplitudeSpinBox"))
        self.gridLayout.addWidget(self.xAmplitudeSpinBox, 1, 0, 1, 1)
        self.xAmplitudeLabel = QtGui.QLabel(self.xAxisControlBox)
        self.xAmplitudeLabel.setObjectName(_fromUtf8("xAmplitudeLabel"))
        self.gridLayout.addWidget(self.xAmplitudeLabel, 1, 1, 1, 1)
        self.xFrequencySpinBox = QtGui.QDoubleSpinBox(self.xAxisControlBox)
        self.xFrequencySpinBox.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.xFrequencySpinBox.setMinimum(0.0)
        self.xFrequencySpinBox.setMaximum(100.0)
        self.xFrequencySpinBox.setSingleStep(0.01)
        self.xFrequencySpinBox.setObjectName(_fromUtf8("xFrequencySpinBox"))
        self.gridLayout.addWidget(self.xFrequencySpinBox, 2, 0, 1, 1)
        self.xFrequencyLabel = QtGui.QLabel(self.xAxisControlBox)
        self.xFrequencyLabel.setObjectName(_fromUtf8("xFrequencyLabel"))
        self.gridLayout.addWidget(self.xFrequencyLabel, 2, 1, 1, 1)
        self.yAxisControlBox = QtGui.QGroupBox(self.focusLockBox)
        self.yAxisControlBox.setGeometry(QtCore.QRect(170, 20, 155, 105))
        self.yAxisControlBox.setObjectName(_fromUtf8("yAxisControlBox"))
        self.gridLayout_2 = QtGui.QGridLayout(self.yAxisControlBox)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.yOffsetSpinBox = QtGui.QDoubleSpinBox(self.yAxisControlBox)
        self.yOffsetSpinBox.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.yOffsetSpinBox.setMinimum(0.0)
        self.yOffsetSpinBox.setMaximum(100.0)
        self.yOffsetSpinBox.setSingleStep(0.01)
        self.yOffsetSpinBox.setObjectName(_fromUtf8("yOffsetSpinBox"))
        self.gridLayout_2.addWidget(self.yOffsetSpinBox, 0, 0, 1, 1)
        self.yOffsetLabel = QtGui.QLabel(self.yAxisControlBox)
        self.yOffsetLabel.setObjectName(_fromUtf8("yOffsetLabel"))
        self.gridLayout_2.addWidget(self.yOffsetLabel, 0, 1, 1, 1)
        self.yAmplitudeSpinBox = QtGui.QDoubleSpinBox(self.yAxisControlBox)
        self.yAmplitudeSpinBox.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.yAmplitudeSpinBox.setMinimum(0.0)
        self.yAmplitudeSpinBox.setMaximum(100.0)
        self.yAmplitudeSpinBox.setSingleStep(0.01)
        self.yAmplitudeSpinBox.setObjectName(_fromUtf8("yAmplitudeSpinBox"))
        self.gridLayout_2.addWidget(self.yAmplitudeSpinBox, 1, 0, 1, 1)
        self.yAmplitudeLabel = QtGui.QLabel(self.yAxisControlBox)
        self.yAmplitudeLabel.setObjectName(_fromUtf8("yAmplitudeLabel"))
        self.gridLayout_2.addWidget(self.yAmplitudeLabel, 1, 1, 1, 1)
        self.yFrequencySpinBox = QtGui.QDoubleSpinBox(self.yAxisControlBox)
        self.yFrequencySpinBox.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.yFrequencySpinBox.setMinimum(0.0)
        self.yFrequencySpinBox.setMaximum(100.0)
        self.yFrequencySpinBox.setSingleStep(0.01)
        self.yFrequencySpinBox.setObjectName(_fromUtf8("yFrequencySpinBox"))
        self.gridLayout_2.addWidget(self.yFrequencySpinBox, 2, 0, 1, 1)
        self.yFrequencyLabel = QtGui.QLabel(self.yAxisControlBox)
        self.yFrequencyLabel.setObjectName(_fromUtf8("yFrequencyLabel"))
        self.gridLayout_2.addWidget(self.yFrequencyLabel, 2, 1, 1, 1)
        self.okButton = QtGui.QPushButton(Dialog)
        self.okButton.setGeometry(QtCore.QRect(280, 150, 75, 24))
        self.okButton.setObjectName(_fromUtf8("okButton"))
        self.activateButton = QtGui.QPushButton(Dialog)
        self.activateButton.setGeometry(QtCore.QRect(10, 150, 75, 24))
        self.activateButton.setObjectName(_fromUtf8("activateButton"))

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "HAL-4000 Galvonometer Control", None))
        self.focusLockBox.setTitle(_translate("Dialog", "Galvonometer Control", None))
        self.xAxisControlBox.setTitle(_translate("Dialog", "X Axis", None))
        self.xOffsetLabel.setText(_translate("Dialog", "Offset (V)", None))
        self.xAmplitudeLabel.setText(_translate("Dialog", "Amplitude (V)", None))
        self.xFrequencyLabel.setText(_translate("Dialog", "Frequency (Hz)", None))
        self.yAxisControlBox.setTitle(_translate("Dialog", "Y Axis", None))
        self.yOffsetLabel.setText(_translate("Dialog", "Offset (V)", None))
        self.yAmplitudeLabel.setText(_translate("Dialog", "Amplitude (V)", None))
        self.yFrequencyLabel.setText(_translate("Dialog", "Frequency (Hz)", None))
        self.okButton.setText(_translate("Dialog", "Ok", None))
        self.activateButton.setText(_translate("Dialog", "Activate", None))

