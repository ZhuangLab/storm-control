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
        GroupBox.resize(237, 219)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(GroupBox.sizePolicy().hasHeightForWidth())
        GroupBox.setSizePolicy(sizePolicy)
        self.verticalLayout = QtWidgets.QVBoxLayout(GroupBox)
        self.verticalLayout.setContentsMargins(0, 9, 0, 0)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.settingsListView = ParametersMVC(GroupBox)
        self.settingsListView.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.settingsListView.setFrameShadow(QtWidgets.QFrame.Plain)
        self.settingsListView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.settingsListView.setObjectName("settingsListView")
        self.verticalLayout.addWidget(self.settingsListView)

        self.retranslateUi(GroupBox)
        QtCore.QMetaObject.connectSlotsByName(GroupBox)

    def retranslateUi(self, GroupBox):
        _translate = QtCore.QCoreApplication.translate
        GroupBox.setWindowTitle(_translate("GroupBox", "GroupBox"))
        GroupBox.setTitle(_translate("GroupBox", "Settings"))

from storm_control.hal4000.settings.parametersListView import ParametersMVC
