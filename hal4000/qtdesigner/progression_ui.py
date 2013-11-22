# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'progression.ui'
#
# Created: Fri Nov 22 08:34:10 2013
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
        Dialog.resize(380, 312)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        Dialog.setMinimumSize(QtCore.QSize(360, 312))
        Dialog.setMaximumSize(QtCore.QSize(380, 312))
        self.progressionsBox = QtGui.QGroupBox(Dialog)
        self.progressionsBox.setGeometry(QtCore.QRect(10, 0, 361, 271))
        self.progressionsBox.setObjectName(_fromUtf8("progressionsBox"))
        self.gridLayout = QtGui.QGridLayout(self.progressionsBox)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.tabWidget = QtGui.QTabWidget(self.progressionsBox)
        self.tabWidget.setObjectName(_fromUtf8("tabWidget"))
        self.linearTab = QtGui.QWidget()
        self.linearTab.setObjectName(_fromUtf8("linearTab"))
        self.channelLabel = QtGui.QLabel(self.linearTab)
        self.channelLabel.setGeometry(QtCore.QRect(10, 10, 46, 14))
        self.channelLabel.setObjectName(_fromUtf8("channelLabel"))
        self.activeLabel = QtGui.QLabel(self.linearTab)
        self.activeLabel.setGeometry(QtCore.QRect(60, 10, 46, 14))
        self.activeLabel.setObjectName(_fromUtf8("activeLabel"))
        self.startLabel = QtGui.QLabel(self.linearTab)
        self.startLabel.setGeometry(QtCore.QRect(120, 10, 46, 14))
        self.startLabel.setObjectName(_fromUtf8("startLabel"))
        self.incrementLabel = QtGui.QLabel(self.linearTab)
        self.incrementLabel.setGeometry(QtCore.QRect(190, 7, 81, 20))
        self.incrementLabel.setObjectName(_fromUtf8("incrementLabel"))
        self.framesLabel = QtGui.QLabel(self.linearTab)
        self.framesLabel.setGeometry(QtCore.QRect(260, 7, 46, 21))
        self.framesLabel.setObjectName(_fromUtf8("framesLabel"))
        self.tabWidget.addTab(self.linearTab, _fromUtf8(""))
        self.expTab = QtGui.QWidget()
        self.expTab.setObjectName(_fromUtf8("expTab"))
        self.framesLabel_2 = QtGui.QLabel(self.expTab)
        self.framesLabel_2.setGeometry(QtCore.QRect(260, 7, 46, 21))
        self.framesLabel_2.setObjectName(_fromUtf8("framesLabel_2"))
        self.activeLabel_2 = QtGui.QLabel(self.expTab)
        self.activeLabel_2.setGeometry(QtCore.QRect(60, 10, 46, 14))
        self.activeLabel_2.setObjectName(_fromUtf8("activeLabel_2"))
        self.startLabel_2 = QtGui.QLabel(self.expTab)
        self.startLabel_2.setGeometry(QtCore.QRect(120, 10, 46, 14))
        self.startLabel_2.setObjectName(_fromUtf8("startLabel_2"))
        self.incrementLabel_2 = QtGui.QLabel(self.expTab)
        self.incrementLabel_2.setGeometry(QtCore.QRect(190, 7, 81, 20))
        self.incrementLabel_2.setObjectName(_fromUtf8("incrementLabel_2"))
        self.channelLabel_2 = QtGui.QLabel(self.expTab)
        self.channelLabel_2.setGeometry(QtCore.QRect(10, 10, 46, 14))
        self.channelLabel_2.setObjectName(_fromUtf8("channelLabel_2"))
        self.tabWidget.addTab(self.expTab, _fromUtf8(""))
        self.fileTab = QtGui.QWidget()
        self.fileTab.setObjectName(_fromUtf8("fileTab"))
        self.powerLabel = QtGui.QLabel(self.fileTab)
        self.powerLabel.setGeometry(QtCore.QRect(10, 10, 61, 16))
        self.powerLabel.setObjectName(_fromUtf8("powerLabel"))
        self.loadFileButton = QtGui.QPushButton(self.fileTab)
        self.loadFileButton.setGeometry(QtCore.QRect(250, 30, 75, 23))
        self.loadFileButton.setObjectName(_fromUtf8("loadFileButton"))
        self.filenameLabel = QtGui.QLabel(self.fileTab)
        self.filenameLabel.setGeometry(QtCore.QRect(70, 10, 261, 16))
        self.filenameLabel.setObjectName(_fromUtf8("filenameLabel"))
        self.tabWidget.addTab(self.fileTab, _fromUtf8(""))
        self.gridLayout.addWidget(self.tabWidget, 0, 0, 1, 1)
        self.okButton = QtGui.QPushButton(Dialog)
        self.okButton.setGeometry(QtCore.QRect(256, 280, 75, 24))
        self.okButton.setObjectName(_fromUtf8("okButton"))
        self.progressionsCheckBox = QtGui.QCheckBox(Dialog)
        self.progressionsCheckBox.setGeometry(QtCore.QRect(10, 280, 151, 18))
        self.progressionsCheckBox.setObjectName(_fromUtf8("progressionsCheckBox"))

        self.retranslateUi(Dialog)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "HAL-4000 Power Progressions", None))
        self.progressionsBox.setTitle(_translate("Dialog", "Power Progressions", None))
        self.channelLabel.setText(_translate("Dialog", "Channel", None))
        self.activeLabel.setText(_translate("Dialog", "Active", None))
        self.startLabel.setText(_translate("Dialog", "Start", None))
        self.incrementLabel.setText(_translate("Dialog", "Increment", None))
        self.framesLabel.setText(_translate("Dialog", "Frames", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.linearTab), _translate("Dialog", "Linear", None))
        self.framesLabel_2.setText(_translate("Dialog", "Frames", None))
        self.activeLabel_2.setText(_translate("Dialog", "Active", None))
        self.startLabel_2.setText(_translate("Dialog", "Start", None))
        self.incrementLabel_2.setText(_translate("Dialog", "Multiplier", None))
        self.channelLabel_2.setText(_translate("Dialog", "Channel", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.expTab), _translate("Dialog", "Exponential", None))
        self.powerLabel.setText(_translate("Dialog", "Power File:", None))
        self.loadFileButton.setText(_translate("Dialog", "Load File", None))
        self.filenameLabel.setText(_translate("Dialog", "None", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.fileTab), _translate("Dialog", "From File", None))
        self.okButton.setText(_translate("Dialog", "Ok", None))
        self.progressionsCheckBox.setText(_translate("Dialog", "Use Power Progressions", None))

