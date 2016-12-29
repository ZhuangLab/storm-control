# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'illumination.ui'
#
# Created by: PyQt5 UI code generator 5.7
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(372, 312)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        Dialog.setMinimumSize(QtCore.QSize(372, 312))
        Dialog.setMaximumSize(QtCore.QSize(372, 312))
        self.powerControlBox = QtWidgets.QGroupBox(Dialog)
        self.powerControlBox.setGeometry(QtCore.QRect(10, 0, 354, 271))
        self.powerControlBox.setObjectName("powerControlBox")
        self.okButton = QtWidgets.QPushButton(Dialog)
        self.okButton.setGeometry(QtCore.QRect(290, 280, 75, 24))
        self.okButton.setObjectName("okButton")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "HAL-4000 Illumination"))
        self.powerControlBox.setTitle(_translate("Dialog", "Power Control"))
        self.okButton.setText(_translate("Dialog", "Ok"))

