# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'qt_valve.ui'
#
# Created by: PyQt5 UI code generator 5.7
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_QtValveControlWidget(object):
    def setupUi(self, QtValveControlWidget):
        QtValveControlWidget.setObjectName("QtValveControlWidget")
        QtValveControlWidget.resize(577, 138)
        self.gridLayout = QtWidgets.QGridLayout(QtValveControlWidget)
        self.gridLayout.setObjectName("gridLayout")
        self.valveGroupBox = QtWidgets.QGroupBox(QtValveControlWidget)
        self.valveGroupBox.setObjectName("valveGroupBox")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.valveGroupBox)
        self.gridLayout_2.setObjectName("gridLayout_2")
        spacerItem = QtWidgets.QSpacerItem(20, 14, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout_2.addItem(spacerItem, 4, 0, 1, 1)
        self.desiredPortLabel = QtWidgets.QLabel(self.valveGroupBox)
        self.desiredPortLabel.setObjectName("desiredPortLabel")
        self.gridLayout_2.addWidget(self.desiredPortLabel, 1, 0, 1, 2)
        self.desiredPortComboBox = QtWidgets.QComboBox(self.valveGroupBox)
        self.desiredPortComboBox.setObjectName("desiredPortComboBox")
        self.desiredPortComboBox.addItem("")
        self.gridLayout_2.addWidget(self.desiredPortComboBox, 2, 0, 2, 2)
        self.valveConfigurationLabel = QtWidgets.QLabel(self.valveGroupBox)
        self.valveConfigurationLabel.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.valveConfigurationLabel.setObjectName("valveConfigurationLabel")
        self.gridLayout_2.addWidget(self.valveConfigurationLabel, 0, 4, 1, 1)
        self.changePortButton = QtWidgets.QPushButton(self.valveGroupBox)
        self.changePortButton.setObjectName("changePortButton")
        self.gridLayout_2.addWidget(self.changePortButton, 2, 4, 2, 1)
        self.rotationDirectionLabel = QtWidgets.QLabel(self.valveGroupBox)
        self.rotationDirectionLabel.setObjectName("rotationDirectionLabel")
        self.gridLayout_2.addWidget(self.rotationDirectionLabel, 1, 2, 1, 2)
        self.desiredRotationComboBox = QtWidgets.QComboBox(self.valveGroupBox)
        self.desiredRotationComboBox.setObjectName("desiredRotationComboBox")
        self.desiredRotationComboBox.addItem("")
        self.desiredRotationComboBox.addItem("")
        self.gridLayout_2.addWidget(self.desiredRotationComboBox, 2, 2, 2, 2)
        self.valveStatusLabel = QtWidgets.QLabel(self.valveGroupBox)
        font = QtGui.QFont()
        font.setPointSize(20)
        self.valveStatusLabel.setFont(font)
        self.valveStatusLabel.setObjectName("valveStatusLabel")
        self.gridLayout_2.addWidget(self.valveStatusLabel, 0, 0, 1, 4)
        self.gridLayout.addWidget(self.valveGroupBox, 0, 0, 1, 1)

        self.retranslateUi(QtValveControlWidget)
        QtCore.QMetaObject.connectSlotsByName(QtValveControlWidget)
        QtValveControlWidget.setTabOrder(self.desiredPortComboBox, self.desiredRotationComboBox)
        QtValveControlWidget.setTabOrder(self.desiredRotationComboBox, self.changePortButton)

    def retranslateUi(self, QtValveControlWidget):
        _translate = QtCore.QCoreApplication.translate
        QtValveControlWidget.setWindowTitle(_translate("QtValveControlWidget", "Form"))
        self.valveGroupBox.setTitle(_translate("QtValveControlWidget", "Valve 1"))
        self.desiredPortLabel.setText(_translate("QtValveControlWidget", "Desired Port"))
        self.desiredPortComboBox.setItemText(0, _translate("QtValveControlWidget", "Position"))
        self.valveConfigurationLabel.setText(_translate("QtValveControlWidget", "Valve Configuration"))
        self.changePortButton.setText(_translate("QtValveControlWidget", "Change Port"))
        self.rotationDirectionLabel.setText(_translate("QtValveControlWidget", "Rotation Direction"))
        self.desiredRotationComboBox.setItemText(0, _translate("QtValveControlWidget", "Clockwise"))
        self.desiredRotationComboBox.setItemText(1, _translate("QtValveControlWidget", "Counter Clockwise"))
        self.valveStatusLabel.setText(_translate("QtValveControlWidget", "Valve Status"))

