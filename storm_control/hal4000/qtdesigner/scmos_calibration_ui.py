# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'scmos-calibration.ui'
#
# Created by: PyQt5 UI code generator 5.7
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(293, 151)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.cameraGroupBox = QtWidgets.QGroupBox(Dialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cameraGroupBox.sizePolicy().hasHeightForWidth())
        self.cameraGroupBox.setSizePolicy(sizePolicy)
        self.cameraGroupBox.setObjectName("cameraGroupBox")
        self.verticalLayout.addWidget(self.cameraGroupBox)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.calibrationFileLabel = QtWidgets.QLabel(Dialog)
        self.calibrationFileLabel.setObjectName("calibrationFileLabel")
        self.horizontalLayout_3.addWidget(self.calibrationFileLabel)
        self.calibrationFileLineEdit = QtWidgets.QLineEdit(Dialog)
        self.calibrationFileLineEdit.setObjectName("calibrationFileLineEdit")
        self.horizontalLayout_3.addWidget(self.calibrationFileLineEdit)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.startButton = QtWidgets.QPushButton(Dialog)
        self.startButton.setObjectName("startButton")
        self.horizontalLayout.addWidget(self.startButton)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.framesLabel = QtWidgets.QLabel(Dialog)
        self.framesLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.framesLabel.setObjectName("framesLabel")
        self.horizontalLayout.addWidget(self.framesLabel)
        self.framesSpinBox = QtWidgets.QSpinBox(Dialog)
        self.framesSpinBox.setMinimum(10)
        self.framesSpinBox.setMaximum(1000000)
        self.framesSpinBox.setProperty("value", 10000)
        self.framesSpinBox.setObjectName("framesSpinBox")
        self.horizontalLayout.addWidget(self.framesSpinBox)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.okButton = QtWidgets.QPushButton(Dialog)
        self.okButton.setObjectName("okButton")
        self.horizontalLayout_2.addWidget(self.okButton)
        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.cameraGroupBox.setTitle(_translate("Dialog", "Cameras"))
        self.calibrationFileLabel.setText(_translate("Dialog", "Calibration File:"))
        self.calibrationFileLineEdit.setText(_translate("Dialog", "dark"))
        self.startButton.setText(_translate("Dialog", "Start"))
        self.framesLabel.setText(_translate("Dialog", "Frames:"))
        self.okButton.setText(_translate("Dialog", "Ok"))

