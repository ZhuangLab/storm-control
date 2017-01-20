# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dualfocuslock.ui'
#
# Created by: PyQt5 UI code generator 5.7
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(811, 310)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        Dialog.setMinimumSize(QtCore.QSize(811, 310))
        Dialog.setMaximumSize(QtCore.QSize(811, 310))
        self.focusLockBox = QtWidgets.QGroupBox(Dialog)
        self.focusLockBox.setGeometry(QtCore.QRect(10, 0, 792, 271))
        self.focusLockBox.setObjectName("focusLockBox")
        self.modeBox = QtWidgets.QGroupBox(self.focusLockBox)
        self.modeBox.setGeometry(QtCore.QRect(10, 20, 181, 151))
        self.modeBox.setObjectName("modeBox")
        self.lockButton = QtWidgets.QPushButton(self.modeBox)
        self.lockButton.setGeometry(QtCore.QRect(110, 90, 61, 24))
        self.lockButton.setObjectName("lockButton")
        self.lockLabel = QtWidgets.QLabel(self.modeBox)
        self.lockLabel.setGeometry(QtCore.QRect(117, 30, 46, 14))
        self.lockLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.lockLabel.setObjectName("lockLabel")
        self.modeWidget = QtWidgets.QWidget(self.modeBox)
        self.modeWidget.setGeometry(QtCore.QRect(7, 12, 101, 131))
        self.modeWidget.setObjectName("modeWidget")
        self.jumpControlBox = QtWidgets.QGroupBox(self.focusLockBox)
        self.jumpControlBox.setGeometry(QtCore.QRect(10, 180, 181, 81))
        self.jumpControlBox.setObjectName("jumpControlBox")
        self.jumpLabel = QtWidgets.QLabel(self.jumpControlBox)
        self.jumpLabel.setGeometry(QtCore.QRect(104, 22, 61, 16))
        self.jumpLabel.setObjectName("jumpLabel")
        self.jumpSpinBox = QtWidgets.QDoubleSpinBox(self.jumpControlBox)
        self.jumpSpinBox.setGeometry(QtCore.QRect(10, 20, 91, 22))
        self.jumpSpinBox.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.jumpSpinBox.setMinimum(-10.0)
        self.jumpSpinBox.setMaximum(10.0)
        self.jumpSpinBox.setSingleStep(0.01)
        self.jumpSpinBox.setObjectName("jumpSpinBox")
        self.jumpPButton = QtWidgets.QPushButton(self.jumpControlBox)
        self.jumpPButton.setGeometry(QtCore.QRect(10, 50, 75, 24))
        self.jumpPButton.setObjectName("jumpPButton")
        self.jumpNButton = QtWidgets.QPushButton(self.jumpControlBox)
        self.jumpNButton.setGeometry(QtCore.QRect(100, 50, 75, 24))
        self.jumpNButton.setObjectName("jumpNButton")
        self.lockDisplay1Widget = QtWidgets.QWidget(self.focusLockBox)
        self.lockDisplay1Widget.setGeometry(QtCore.QRect(193, 20, 298, 249))
        self.lockDisplay1Widget.setObjectName("lockDisplay1Widget")
        self.lockDisplay2Widget = QtWidgets.QWidget(self.focusLockBox)
        self.lockDisplay2Widget.setGeometry(QtCore.QRect(494, 20, 298, 249))
        self.lockDisplay2Widget.setObjectName("lockDisplay2Widget")
        self.okButton = QtWidgets.QPushButton(Dialog)
        self.okButton.setGeometry(QtCore.QRect(730, 280, 75, 24))
        self.okButton.setObjectName("okButton")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "HAL-4000 Focus Lock"))
        self.focusLockBox.setTitle(_translate("Dialog", "Focus Lock Control"))
        self.modeBox.setTitle(_translate("Dialog", "Mode"))
        self.lockButton.setText(_translate("Dialog", "Lock"))
        self.lockLabel.setText(_translate("Dialog", "Locked"))
        self.jumpControlBox.setTitle(_translate("Dialog", "Jump Control"))
        self.jumpLabel.setText(_translate("Dialog", "Offset (um)"))
        self.jumpPButton.setText(_translate("Dialog", "Jump (+)"))
        self.jumpNButton.setText(_translate("Dialog", "Jump (-)"))
        self.okButton.setText(_translate("Dialog", "Ok"))

