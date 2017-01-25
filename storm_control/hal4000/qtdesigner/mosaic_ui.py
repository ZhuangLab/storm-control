# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mosaic.ui'
#
# Created by: PyQt5 UI code generator 5.7
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_GroupBox(object):
    def setupUi(self, GroupBox):
        GroupBox.setObjectName("GroupBox")
        GroupBox.resize(330, 183)
        self.horizontalLayout = QtWidgets.QHBoxLayout(GroupBox)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.objectiveLabel = QtWidgets.QLabel(GroupBox)
        self.objectiveLabel.setObjectName("objectiveLabel")
        self.horizontalLayout.addWidget(self.objectiveLabel)
        self.objectiveText = QtWidgets.QLabel(GroupBox)
        self.objectiveText.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.objectiveText.setObjectName("objectiveText")
        self.horizontalLayout.addWidget(self.objectiveText)

        self.retranslateUi(GroupBox)
        QtCore.QMetaObject.connectSlotsByName(GroupBox)

    def retranslateUi(self, GroupBox):
        _translate = QtCore.QCoreApplication.translate
        GroupBox.setWindowTitle(_translate("GroupBox", "GroupBox"))
        GroupBox.setTitle(_translate("GroupBox", "Mosaic"))
        self.objectiveLabel.setText(_translate("GroupBox", "Objective:"))
        self.objectiveText.setText(_translate("GroupBox", "asdf"))

