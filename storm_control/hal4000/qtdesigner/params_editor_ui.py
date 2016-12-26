# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'params-editor.ui'
#
# Created by: PyQt5 UI code generator 5.7
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(845, 654)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        Dialog.setMinimumSize(QtCore.QSize(100, 100))
        Dialog.setMaximumSize(QtCore.QSize(10000, 10000))
        self.gridLayout = QtWidgets.QGridLayout(Dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.editTabWidget = QtWidgets.QTabWidget(Dialog)
        self.editTabWidget.setObjectName("editTabWidget")
        self.Main = QtWidgets.QWidget()
        self.Main.setObjectName("Main")
        self.editTabWidget.addTab(self.Main, "")
        self.tab2 = QtWidgets.QWidget()
        self.tab2.setObjectName("tab2")
        self.editTabWidget.addTab(self.tab2, "")
        self.verticalLayout.addWidget(self.editTabWidget)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.updateButton = QtWidgets.QPushButton(Dialog)
        self.updateButton.setObjectName("updateButton")
        self.horizontalLayout.addWidget(self.updateButton)
        self.okButton = QtWidgets.QPushButton(Dialog)
        self.okButton.setObjectName("okButton")
        self.horizontalLayout.addWidget(self.okButton)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.gridLayout.addLayout(self.verticalLayout, 1, 0, 1, 1)
        self.parametersNameLabel = QtWidgets.QLabel(Dialog)
        self.parametersNameLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.parametersNameLabel.setObjectName("parametersNameLabel")
        self.gridLayout.addWidget(self.parametersNameLabel, 0, 0, 1, 1)

        self.retranslateUi(Dialog)
        self.editTabWidget.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "HAL-4000 Parameters Editor"))
        self.editTabWidget.setTabText(self.editTabWidget.indexOf(self.Main), _translate("Dialog", "Main"))
        self.editTabWidget.setTabText(self.editTabWidget.indexOf(self.tab2), _translate("Dialog", "Tab 2"))
        self.updateButton.setText(_translate("Dialog", "Update"))
        self.okButton.setText(_translate("Dialog", "Ok"))
        self.parametersNameLabel.setText(_translate("Dialog", "NA"))

