# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'qt_valve.ui'
#
# Created: Sat Dec 21 17:54:55 2013
#      by: PyQt4 UI code generator 4.10.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_QtValveControlWidget(object):
    def setupUi(self, QtValveControlWidget):
        QtValveControlWidget.setObjectName(_fromUtf8("QtValveControlWidget"))
        QtValveControlWidget.resize(577, 138)
        self.gridLayout = QtGui.QGridLayout(QtValveControlWidget)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.valveGroupBox = QtGui.QGroupBox(QtValveControlWidget)
        self.valveGroupBox.setObjectName(_fromUtf8("valveGroupBox"))
        self.gridLayout_2 = QtGui.QGridLayout(self.valveGroupBox)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        spacerItem = QtGui.QSpacerItem(20, 14, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout_2.addItem(spacerItem, 4, 0, 1, 1)
        self.desiredPortLabel = QtGui.QLabel(self.valveGroupBox)
        self.desiredPortLabel.setObjectName(_fromUtf8("desiredPortLabel"))
        self.gridLayout_2.addWidget(self.desiredPortLabel, 1, 0, 1, 2)
        self.desiredPortComboBox = QtGui.QComboBox(self.valveGroupBox)
        self.desiredPortComboBox.setObjectName(_fromUtf8("desiredPortComboBox"))
        self.desiredPortComboBox.addItem(_fromUtf8(""))
        self.gridLayout_2.addWidget(self.desiredPortComboBox, 2, 0, 2, 2)
        self.valveConfigurationLabel = QtGui.QLabel(self.valveGroupBox)
        self.valveConfigurationLabel.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.valveConfigurationLabel.setObjectName(_fromUtf8("valveConfigurationLabel"))
        self.gridLayout_2.addWidget(self.valveConfigurationLabel, 0, 4, 1, 1)
        self.changePortButton = QtGui.QPushButton(self.valveGroupBox)
        self.changePortButton.setObjectName(_fromUtf8("changePortButton"))
        self.gridLayout_2.addWidget(self.changePortButton, 2, 4, 2, 1)
        self.rotationDirectionLabel = QtGui.QLabel(self.valveGroupBox)
        self.rotationDirectionLabel.setObjectName(_fromUtf8("rotationDirectionLabel"))
        self.gridLayout_2.addWidget(self.rotationDirectionLabel, 1, 2, 1, 2)
        self.desiredRotationComboBox = QtGui.QComboBox(self.valveGroupBox)
        self.desiredRotationComboBox.setObjectName(_fromUtf8("desiredRotationComboBox"))
        self.desiredRotationComboBox.addItem(_fromUtf8(""))
        self.desiredRotationComboBox.addItem(_fromUtf8(""))
        self.gridLayout_2.addWidget(self.desiredRotationComboBox, 2, 2, 2, 2)
        self.valveStatusLabel = QtGui.QLabel(self.valveGroupBox)
        font = QtGui.QFont()
        font.setPointSize(20)
        self.valveStatusLabel.setFont(font)
        self.valveStatusLabel.setObjectName(_fromUtf8("valveStatusLabel"))
        self.gridLayout_2.addWidget(self.valveStatusLabel, 0, 0, 1, 4)
        self.gridLayout.addWidget(self.valveGroupBox, 0, 0, 1, 1)

        self.retranslateUi(QtValveControlWidget)
        QtCore.QMetaObject.connectSlotsByName(QtValveControlWidget)
        QtValveControlWidget.setTabOrder(self.desiredPortComboBox, self.desiredRotationComboBox)
        QtValveControlWidget.setTabOrder(self.desiredRotationComboBox, self.changePortButton)

    def retranslateUi(self, QtValveControlWidget):
        QtValveControlWidget.setWindowTitle(_translate("QtValveControlWidget", "Form", None))
        self.valveGroupBox.setTitle(_translate("QtValveControlWidget", "Valve 1", None))
        self.desiredPortLabel.setText(_translate("QtValveControlWidget", "Desired Port", None))
        self.desiredPortComboBox.setItemText(0, _translate("QtValveControlWidget", "Position", None))
        self.valveConfigurationLabel.setText(_translate("QtValveControlWidget", "Valve Configuration", None))
        self.changePortButton.setText(_translate("QtValveControlWidget", "Change Port", None))
        self.rotationDirectionLabel.setText(_translate("QtValveControlWidget", "Rotation Direction", None))
        self.desiredRotationComboBox.setItemText(0, _translate("QtValveControlWidget", "Clockwise", None))
        self.desiredRotationComboBox.setItemText(1, _translate("QtValveControlWidget", "Counter Clockwise", None))
        self.valveStatusLabel.setText(_translate("QtValveControlWidget", "Valve Status", None))


class QtValveControlWidget(QtGui.QWidget, Ui_QtValveControlWidget):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QWidget.__init__(self, parent, f)

        self.setupUi(self)

