# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'storm4-misc.ui'
#
# Created by: PyQt5 UI code generator 5.7
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(391, 105)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        Dialog.setMinimumSize(QtCore.QSize(391, 105))
        Dialog.setMaximumSize(QtCore.QSize(391, 105))
        Dialog.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        self.okButton = QtWidgets.QPushButton(Dialog)
        self.okButton.setGeometry(QtCore.QRect(300, 70, 75, 24))
        self.okButton.setCheckable(False)
        self.okButton.setObjectName("okButton")
        self.filterWheelGroupBox = QtWidgets.QGroupBox(Dialog)
        self.filterWheelGroupBox.setGeometry(QtCore.QRect(10, 10, 371, 51))
        self.filterWheelGroupBox.setObjectName("filterWheelGroupBox")
        self.filter1Button = QtWidgets.QPushButton(self.filterWheelGroupBox)
        self.filter1Button.setGeometry(QtCore.QRect(10, 20, 51, 24))
        self.filter1Button.setCheckable(True)
        self.filter1Button.setAutoExclusive(True)
        self.filter1Button.setObjectName("filter1Button")
        self.filter2Button = QtWidgets.QPushButton(self.filterWheelGroupBox)
        self.filter2Button.setGeometry(QtCore.QRect(70, 20, 51, 24))
        self.filter2Button.setCheckable(True)
        self.filter2Button.setAutoExclusive(True)
        self.filter2Button.setObjectName("filter2Button")
        self.filter3Button = QtWidgets.QPushButton(self.filterWheelGroupBox)
        self.filter3Button.setGeometry(QtCore.QRect(130, 20, 51, 24))
        self.filter3Button.setCheckable(True)
        self.filter3Button.setAutoExclusive(True)
        self.filter3Button.setObjectName("filter3Button")
        self.filter4Button = QtWidgets.QPushButton(self.filterWheelGroupBox)
        self.filter4Button.setGeometry(QtCore.QRect(190, 20, 51, 24))
        self.filter4Button.setCheckable(True)
        self.filter4Button.setAutoExclusive(True)
        self.filter4Button.setObjectName("filter4Button")
        self.filter5Button = QtWidgets.QPushButton(self.filterWheelGroupBox)
        self.filter5Button.setGeometry(QtCore.QRect(250, 20, 51, 24))
        self.filter5Button.setCheckable(True)
        self.filter5Button.setAutoExclusive(True)
        self.filter5Button.setObjectName("filter5Button")
        self.filter6Button = QtWidgets.QPushButton(self.filterWheelGroupBox)
        self.filter6Button.setGeometry(QtCore.QRect(310, 20, 51, 24))
        self.filter6Button.setCheckable(True)
        self.filter6Button.setAutoExclusive(True)
        self.filter6Button.setObjectName("filter6Button")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "HAL-4000 Miscellaneous Controls"))
        self.okButton.setText(_translate("Dialog", "Ok"))
        self.filterWheelGroupBox.setTitle(_translate("Dialog", "Filter Wheel Control"))
        self.filter1Button.setText(_translate("Dialog", "1"))
        self.filter2Button.setText(_translate("Dialog", "2"))
        self.filter3Button.setText(_translate("Dialog", "3"))
        self.filter4Button.setText(_translate("Dialog", "4"))
        self.filter5Button.setText(_translate("Dialog", "5"))
        self.filter6Button.setText(_translate("Dialog", "6"))

