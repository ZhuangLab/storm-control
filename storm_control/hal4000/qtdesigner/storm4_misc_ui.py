# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'storm4-misc.ui'
#
# Created: Mon Sep 28 08:55:22 2015
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

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(391, 105)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        Dialog.setMinimumSize(QtCore.QSize(391, 105))
        Dialog.setMaximumSize(QtCore.QSize(391, 105))
        Dialog.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        self.okButton = QtGui.QPushButton(Dialog)
        self.okButton.setGeometry(QtCore.QRect(300, 70, 75, 24))
        self.okButton.setCheckable(False)
        self.okButton.setObjectName(_fromUtf8("okButton"))
        self.filterWheelGroupBox = QtGui.QGroupBox(Dialog)
        self.filterWheelGroupBox.setGeometry(QtCore.QRect(10, 10, 371, 51))
        self.filterWheelGroupBox.setObjectName(_fromUtf8("filterWheelGroupBox"))
        self.filter1Button = QtGui.QPushButton(self.filterWheelGroupBox)
        self.filter1Button.setGeometry(QtCore.QRect(10, 20, 51, 24))
        self.filter1Button.setCheckable(True)
        self.filter1Button.setAutoExclusive(True)
        self.filter1Button.setObjectName(_fromUtf8("filter1Button"))
        self.filter2Button = QtGui.QPushButton(self.filterWheelGroupBox)
        self.filter2Button.setGeometry(QtCore.QRect(70, 20, 51, 24))
        self.filter2Button.setCheckable(True)
        self.filter2Button.setAutoExclusive(True)
        self.filter2Button.setObjectName(_fromUtf8("filter2Button"))
        self.filter3Button = QtGui.QPushButton(self.filterWheelGroupBox)
        self.filter3Button.setGeometry(QtCore.QRect(130, 20, 51, 24))
        self.filter3Button.setCheckable(True)
        self.filter3Button.setAutoExclusive(True)
        self.filter3Button.setObjectName(_fromUtf8("filter3Button"))
        self.filter4Button = QtGui.QPushButton(self.filterWheelGroupBox)
        self.filter4Button.setGeometry(QtCore.QRect(190, 20, 51, 24))
        self.filter4Button.setCheckable(True)
        self.filter4Button.setAutoExclusive(True)
        self.filter4Button.setObjectName(_fromUtf8("filter4Button"))
        self.filter5Button = QtGui.QPushButton(self.filterWheelGroupBox)
        self.filter5Button.setGeometry(QtCore.QRect(250, 20, 51, 24))
        self.filter5Button.setCheckable(True)
        self.filter5Button.setAutoExclusive(True)
        self.filter5Button.setObjectName(_fromUtf8("filter5Button"))
        self.filter6Button = QtGui.QPushButton(self.filterWheelGroupBox)
        self.filter6Button.setGeometry(QtCore.QRect(310, 20, 51, 24))
        self.filter6Button.setCheckable(True)
        self.filter6Button.setAutoExclusive(True)
        self.filter6Button.setObjectName(_fromUtf8("filter6Button"))

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "HAL-4000 Miscellaneous Controls", None))
        self.okButton.setText(_translate("Dialog", "Ok", None))
        self.filterWheelGroupBox.setTitle(_translate("Dialog", "Filter Wheel Control", None))
        self.filter1Button.setText(_translate("Dialog", "1", None))
        self.filter2Button.setText(_translate("Dialog", "2", None))
        self.filter3Button.setText(_translate("Dialog", "3", None))
        self.filter4Button.setText(_translate("Dialog", "4", None))
        self.filter5Button.setText(_translate("Dialog", "5", None))
        self.filter6Button.setText(_translate("Dialog", "6", None))

