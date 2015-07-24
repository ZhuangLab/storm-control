# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'camera-params.ui'
#
# Created: Thu Jul 23 21:28:28 2015
#      by: PyQt4 UI code generator 4.11.3
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
        self.verticalLayout = QtGui.QVBoxLayout(GroupBox)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setMargin(2)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.EMCCDLabel = QtGui.QLabel(GroupBox)
        self.EMCCDLabel.setObjectName(_fromUtf8("EMCCDLabel"))
        self.horizontalLayout.addWidget(self.EMCCDLabel)
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
        self.horizontalLayout.addWidget(self.EMCCDSlider)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.preampGainLabel = QtGui.QLabel(GroupBox)
        self.preampGainLabel.setObjectName(_fromUtf8("preampGainLabel"))
        self.horizontalLayout_2.addWidget(self.preampGainLabel)
        self.preampGainText = QtGui.QLabel(GroupBox)
        self.preampGainText.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.preampGainText.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.preampGainText.setObjectName(_fromUtf8("preampGainText"))
        self.horizontalLayout_2.addWidget(self.preampGainText)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.pictureSizeLabel = QtGui.QLabel(GroupBox)
        self.pictureSizeLabel.setObjectName(_fromUtf8("pictureSizeLabel"))
        self.horizontalLayout_3.addWidget(self.pictureSizeLabel)
        self.pictureSizeText = QtGui.QLabel(GroupBox)
        self.pictureSizeText.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.pictureSizeText.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.pictureSizeText.setObjectName(_fromUtf8("pictureSizeText"))
        self.horizontalLayout_3.addWidget(self.pictureSizeText)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_4 = QtGui.QHBoxLayout()
        self.horizontalLayout_4.setObjectName(_fromUtf8("horizontalLayout_4"))
        self.exposureTimeLabel = QtGui.QLabel(GroupBox)
        self.exposureTimeLabel.setObjectName(_fromUtf8("exposureTimeLabel"))
        self.horizontalLayout_4.addWidget(self.exposureTimeLabel)
        self.exposureTimeText = QtGui.QLabel(GroupBox)
        self.exposureTimeText.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.exposureTimeText.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.exposureTimeText.setObjectName(_fromUtf8("exposureTimeText"))
        self.horizontalLayout_4.addWidget(self.exposureTimeText)
        self.verticalLayout.addLayout(self.horizontalLayout_4)
        self.horizontalLayout_5 = QtGui.QHBoxLayout()
        self.horizontalLayout_5.setObjectName(_fromUtf8("horizontalLayout_5"))
        self.FPSLabel = QtGui.QLabel(GroupBox)
        self.FPSLabel.setObjectName(_fromUtf8("FPSLabel"))
        self.horizontalLayout_5.addWidget(self.FPSLabel)
        self.FPSText = QtGui.QLabel(GroupBox)
        self.FPSText.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.FPSText.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.FPSText.setObjectName(_fromUtf8("FPSText"))
        self.horizontalLayout_5.addWidget(self.FPSText)
        self.verticalLayout.addLayout(self.horizontalLayout_5)
        self.horizontalLayout_6 = QtGui.QHBoxLayout()
        self.horizontalLayout_6.setObjectName(_fromUtf8("horizontalLayout_6"))
        self.temperatureLabel = QtGui.QLabel(GroupBox)
        self.temperatureLabel.setObjectName(_fromUtf8("temperatureLabel"))
        self.horizontalLayout_6.addWidget(self.temperatureLabel)
        self.temperatureText = QtGui.QLabel(GroupBox)
        self.temperatureText.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.temperatureText.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.temperatureText.setObjectName(_fromUtf8("temperatureText"))
        self.horizontalLayout_6.addWidget(self.temperatureText)
        self.verticalLayout.addLayout(self.horizontalLayout_6)

        self.retranslateUi(GroupBox)
        QtCore.QMetaObject.connectSlotsByName(GroupBox)

    def retranslateUi(self, GroupBox):
        GroupBox.setWindowTitle(_translate("GroupBox", "GroupBox", None))
        GroupBox.setTitle(_translate("GroupBox", "Camera", None))
        self.EMCCDLabel.setText(_translate("GroupBox", "EMCCD Gain: 0", None))
        self.preampGainLabel.setText(_translate("GroupBox", "Preamp Gain:", None))
        self.preampGainText.setText(_translate("GroupBox", "asdf", None))
        self.pictureSizeLabel.setText(_translate("GroupBox", "Picture Size:", None))
        self.pictureSizeText.setText(_translate("GroupBox", "asdf", None))
        self.exposureTimeLabel.setText(_translate("GroupBox", "Exposure Time (s):", None))
        self.exposureTimeText.setText(_translate("GroupBox", "asdf", None))
        self.FPSLabel.setText(_translate("GroupBox", "FPS (Hz):", None))
        self.FPSText.setText(_translate("GroupBox", "asdf", None))
        self.temperatureLabel.setText(_translate("GroupBox", "Temperature (C):", None))
        self.temperatureText.setText(_translate("GroupBox", "asdf", None))

