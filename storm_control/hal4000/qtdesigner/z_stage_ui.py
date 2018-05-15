# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'z-stage.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(101, 143)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.groupBox = QtWidgets.QGroupBox(Dialog)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName("verticalLayout")
        self.zPosDoubleSpinBox = QtWidgets.QDoubleSpinBox(self.groupBox)
        self.zPosDoubleSpinBox.setMinimumSize(QtCore.QSize(75, 0))
        self.zPosDoubleSpinBox.setDecimals(3)
        self.zPosDoubleSpinBox.setMinimum(-10000.0)
        self.zPosDoubleSpinBox.setMaximum(10000.0)
        self.zPosDoubleSpinBox.setSingleStep(0.1)
        self.zPosDoubleSpinBox.setObjectName("zPosDoubleSpinBox")
        self.verticalLayout.addWidget(self.zPosDoubleSpinBox)
        self.homeButton = QtWidgets.QPushButton(self.groupBox)
        self.homeButton.setObjectName("homeButton")
        self.verticalLayout.addWidget(self.homeButton)
        self.retractButton = QtWidgets.QPushButton(self.groupBox)
        self.retractButton.setObjectName("retractButton")
        self.verticalLayout.addWidget(self.retractButton)
        self.zeroButton = QtWidgets.QPushButton(self.groupBox)
        self.zeroButton.setObjectName("zeroButton")
        self.verticalLayout.addWidget(self.zeroButton)
        self.verticalLayout_2.addWidget(self.groupBox)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem)
        self.okButton = QtWidgets.QPushButton(Dialog)
        self.okButton.setObjectName("okButton")
        self.verticalLayout_2.addWidget(self.okButton)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.groupBox.setTitle(_translate("Dialog", "Z Stage"))
        self.homeButton.setText(_translate("Dialog", "Home"))
        self.retractButton.setText(_translate("Dialog", "Retract"))
        self.zeroButton.setText(_translate("Dialog", "Zero"))
        self.okButton.setText(_translate("Dialog", "Ok"))

