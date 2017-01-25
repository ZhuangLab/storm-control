# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'settings.ui'
#
# Created by: PyQt5 UI code generator 5.7
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_GroupBox(object):
    def setupUi(self, GroupBox):
        GroupBox.setObjectName("GroupBox")
        GroupBox.resize(237, 184)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(GroupBox.sizePolicy().hasHeightForWidth())
        GroupBox.setSizePolicy(sizePolicy)
        self.verticalLayout = QtWidgets.QVBoxLayout(GroupBox)
        self.verticalLayout.setObjectName("verticalLayout")
        self.settingsScrollArea = QtWidgets.QScrollArea(GroupBox)
        self.settingsScrollArea.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.settingsScrollArea.setWidgetResizable(True)
        self.settingsScrollArea.setObjectName("settingsScrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 211, 148))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.settingsScrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout.addWidget(self.settingsScrollArea)

        self.retranslateUi(GroupBox)
        QtCore.QMetaObject.connectSlotsByName(GroupBox)

    def retranslateUi(self, GroupBox):
        _translate = QtCore.QCoreApplication.translate
        GroupBox.setWindowTitle(_translate("GroupBox", "GroupBox"))
        GroupBox.setTitle(_translate("GroupBox", "Settings"))

