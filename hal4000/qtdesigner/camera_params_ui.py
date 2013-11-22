# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'camera-params.ui'
#
# Created: Fri Nov 22 08:34:06 2013
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

class Ui_GroupBox(object):
    def setupUi(self, GroupBox):
        GroupBox.setObjectName(_fromUtf8("GroupBox"))
        GroupBox.resize(232, 174)
        self.gridLayout = QtGui.QGridLayout(GroupBox)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.preampGainLabel = QtGui.QLabel(GroupBox)
        self.preampGainLabel.setObjectName(_fromUtf8("preampGainLabel"))
        self.gridLayout.addWidget(self.preampGainLabel, 3, 0, 1, 1)
        self.pictureSizeLabel = QtGui.QLabel(GroupBox)
        self.pictureSizeLabel.setObjectName(_fromUtf8("pictureSizeLabel"))
        self.gridLayout.addWidget(self.pictureSizeLabel, 4, 0, 1, 1)
        self.exposureTimeLabel = QtGui.QLabel(GroupBox)
        self.exposureTimeLabel.setObjectName(_fromUtf8("exposureTimeLabel"))
        self.gridLayout.addWidget(self.exposureTimeLabel, 5, 0, 1, 1)
        self.FPSLabel = QtGui.QLabel(GroupBox)
        self.FPSLabel.setObjectName(_fromUtf8("FPSLabel"))
        self.gridLayout.addWidget(self.FPSLabel, 6, 0, 1, 1)
        self.EMCCDLabel = QtGui.QLabel(GroupBox)
        self.EMCCDLabel.setObjectName(_fromUtf8("EMCCDLabel"))
        self.gridLayout.addWidget(self.EMCCDLabel, 1, 0, 1, 1)
        self.EMCCDSlider = QtGui.QSlider(GroupBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.EMCCDSlider.sizePolicy().hasHeightForWidth())
        self.EMCCDSlider.setSizePolicy(sizePolicy)
        self.EMCCDSlider.setMinimumSize(QtCore.QSize(110, 0))
        self.EMCCDSlider.setMaximum(100)
        self.EMCCDSlider.setProperty("value", 0)
        self.EMCCDSlider.setOrientation(QtCore.Qt.Horizontal)
        self.EMCCDSlider.setObjectName(_fromUtf8("EMCCDSlider"))
        self.gridLayout.addWidget(self.EMCCDSlider, 1, 1, 1, 1)
        self.temperatureLabel = QtGui.QLabel(GroupBox)
        self.temperatureLabel.setObjectName(_fromUtf8("temperatureLabel"))
        self.gridLayout.addWidget(self.temperatureLabel, 7, 0, 1, 1)
        self.temperatureText = QtGui.QLabel(GroupBox)
        self.temperatureText.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.temperatureText.setText(_fromUtf8(""))
        self.temperatureText.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.temperatureText.setObjectName(_fromUtf8("temperatureText"))
        self.gridLayout.addWidget(self.temperatureText, 7, 1, 1, 2)
        self.preampGainText = QtGui.QLabel(GroupBox)
        self.preampGainText.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.preampGainText.setText(_fromUtf8(""))
        self.preampGainText.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.preampGainText.setObjectName(_fromUtf8("preampGainText"))
        self.gridLayout.addWidget(self.preampGainText, 3, 1, 1, 2)
        self.pictureSizeText = QtGui.QLabel(GroupBox)
        self.pictureSizeText.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.pictureSizeText.setText(_fromUtf8(""))
        self.pictureSizeText.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.pictureSizeText.setObjectName(_fromUtf8("pictureSizeText"))
        self.gridLayout.addWidget(self.pictureSizeText, 4, 1, 1, 2)
        self.FPSText = QtGui.QLabel(GroupBox)
        self.FPSText.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.FPSText.setText(_fromUtf8(""))
        self.FPSText.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.FPSText.setObjectName(_fromUtf8("FPSText"))
        self.gridLayout.addWidget(self.FPSText, 6, 1, 1, 2)
        self.exposureTimeText = QtGui.QLabel(GroupBox)
        self.exposureTimeText.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.exposureTimeText.setText(_fromUtf8(""))
        self.exposureTimeText.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.exposureTimeText.setObjectName(_fromUtf8("exposureTimeText"))
        self.gridLayout.addWidget(self.exposureTimeText, 5, 1, 1, 2)

        self.retranslateUi(GroupBox)
        QtCore.QMetaObject.connectSlotsByName(GroupBox)

    def retranslateUi(self, GroupBox):
        GroupBox.setWindowTitle(_translate("GroupBox", "GroupBox", None))
        GroupBox.setTitle(_translate("GroupBox", "Camera", None))
        self.preampGainLabel.setText(_translate("GroupBox", "Preamp Gain:", None))
        self.pictureSizeLabel.setText(_translate("GroupBox", "Picture Size:", None))
        self.exposureTimeLabel.setText(_translate("GroupBox", "Exposure Time (s):", None))
        self.FPSLabel.setText(_translate("GroupBox", "FPS (Hz):", None))
        self.EMCCDLabel.setText(_translate("GroupBox", "EMCCD Gain: 0", None))
        self.temperatureLabel.setText(_translate("GroupBox", "Temperature (C):", None))

