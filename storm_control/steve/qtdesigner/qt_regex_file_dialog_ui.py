# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'qt_regex_file_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.7
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(655, 468)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.nameLabel = QtWidgets.QLabel(Dialog)
        self.nameLabel.setObjectName("nameLabel")
        self.horizontalLayout.addWidget(self.nameLabel)
        self.nameLineEdit = QtWidgets.QLineEdit(Dialog)
        self.nameLineEdit.setObjectName("nameLineEdit")
        self.horizontalLayout.addWidget(self.nameLineEdit)
        self.frameNumLabel = QtWidgets.QLabel(Dialog)
        self.frameNumLabel.setObjectName("frameNumLabel")
        self.horizontalLayout.addWidget(self.frameNumLabel)
        self.frameNumSpinBox = QtWidgets.QSpinBox(Dialog)
        self.frameNumSpinBox.setObjectName("frameNumSpinBox")
        self.horizontalLayout.addWidget(self.frameNumSpinBox)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.nameLabel.setText(_translate("Dialog", "Name Filter:"))
        self.frameNumLabel.setText(_translate("Dialog", "Frame Number:"))

