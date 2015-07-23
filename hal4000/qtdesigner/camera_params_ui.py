# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'camera-params.ui'
#
# Created: Thu Jul 23 15:43:22 2015
#      by: PyQt4 UI code generator 4.10.4
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
        GroupBox.resize(276, 185)
        self.horizontalLayout = QtGui.QHBoxLayout(GroupBox)
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setMargin(2)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.verticalLayout_2 = QtGui.QVBoxLayout()
        self.verticalLayout_2.setMargin(2)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.EMCCDLabel = QtGui.QLabel(GroupBox)
        self.EMCCDLabel.setObjectName(_fromUtf8("EMCCDLabel"))
        self.verticalLayout_2.addWidget(self.EMCCDLabel)
        self.preampGainLabel = QtGui.QLabel(GroupBox)
        self.preampGainLabel.setObjectName(_fromUtf8("preampGainLabel"))
        self.verticalLayout_2.addWidget(self.preampGainLabel)
        self.pictureSizeLabel = QtGui.QLabel(GroupBox)
        self.pictureSizeLabel.setObjectName(_fromUtf8("pictureSizeLabel"))
        self.verticalLayout_2.addWidget(self.pictureSizeLabel)
        self.exposureTimeLabel = QtGui.QLabel(GroupBox)
        self.exposureTimeLabel.setObjectName(_fromUtf8("exposureTimeLabel"))
        self.verticalLayout_2.addWidget(self.exposureTimeLabel)
        self.FPSLabel = QtGui.QLabel(GroupBox)
        self.FPSLabel.setObjectName(_fromUtf8("FPSLabel"))
        self.verticalLayout_2.addWidget(self.FPSLabel)
        self.temperatureLabel = QtGui.QLabel(GroupBox)
        self.temperatureLabel.setObjectName(_fromUtf8("temperatureLabel"))
        self.verticalLayout_2.addWidget(self.temperatureLabel)
        self.horizontalLayout.addLayout(self.verticalLayout_2)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setMargin(2)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.EMCCDSlider = QtGui.QSlider(GroupBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.EMCCDSlider.sizePolicy().hasHeightForWidth())
        self.EMCCDSlider.setSizePolicy(sizePolicy)
        self.EMCCDSlider.setMinimumSize(QtCore.QSize(0, 0))
        self.EMCCDSlider.setMaximum(100)
        self.EMCCDSlider.setProperty("value", 0)
        self.EMCCDSlider.setOrientation(QtCore.Qt.Horizontal)
        self.EMCCDSlider.setObjectName(_fromUtf8("EMCCDSlider"))
        self.verticalLayout.addWidget(self.EMCCDSlider)
        self.preampGainText = QtGui.QLabel(GroupBox)
        self.preampGainText.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.preampGainText.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.preampGainText.setObjectName(_fromUtf8("preampGainText"))
        self.verticalLayout.addWidget(self.preampGainText)
        self.pictureSizeText = QtGui.QLabel(GroupBox)
        self.pictureSizeText.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.pictureSizeText.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.pictureSizeText.setObjectName(_fromUtf8("pictureSizeText"))
        self.verticalLayout.addWidget(self.pictureSizeText)
        self.exposureTimeText = QtGui.QLabel(GroupBox)
        self.exposureTimeText.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.exposureTimeText.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.exposureTimeText.setObjectName(_fromUtf8("exposureTimeText"))
        self.verticalLayout.addWidget(self.exposureTimeText)
        self.FPSText = QtGui.QLabel(GroupBox)
        self.FPSText.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.FPSText.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.FPSText.setObjectName(_fromUtf8("FPSText"))
        self.verticalLayout.addWidget(self.FPSText)
        self.temperatureText = QtGui.QLabel(GroupBox)
        self.temperatureText.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.temperatureText.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.temperatureText.setObjectName(_fromUtf8("temperatureText"))
        self.verticalLayout.addWidget(self.temperatureText)
        self.horizontalLayout.addLayout(self.verticalLayout)

        self.retranslateUi(GroupBox)
        QtCore.QMetaObject.connectSlotsByName(GroupBox)

    def retranslateUi(self, GroupBox):
        GroupBox.setWindowTitle(_translate("GroupBox", "GroupBox", None))
        GroupBox.setTitle(_translate("GroupBox", "Camera", None))
        self.EMCCDLabel.setText(_translate("GroupBox", "EMCCD Gain: 0", None))
        self.preampGainLabel.setText(_translate("GroupBox", "Preamp Gain:", None))
        self.pictureSizeLabel.setText(_translate("GroupBox", "Picture Size:", None))
        self.exposureTimeLabel.setText(_translate("GroupBox", "Exposure Time (s):", None))
        self.FPSLabel.setText(_translate("GroupBox", "FPS (Hz):", None))
        self.temperatureLabel.setText(_translate("GroupBox", "Temperature (C):", None))
        self.preampGainText.setText(_translate("GroupBox", "asdf", None))
        self.pictureSizeText.setText(_translate("GroupBox", "asdf", None))
        self.exposureTimeText.setText(_translate("GroupBox", "asdf", None))
        self.FPSText.setText(_translate("GroupBox", "asdf", None))
        self.temperatureText.setText(_translate("GroupBox", "asdf", None))

