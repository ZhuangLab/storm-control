# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'qt_valve.ui'
#
# Created: Sat Dec 21 16:41:42 2013
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

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName(_fromUtf8("Form"))
        Form.resize(577, 138)
        self.gridLayout = QtGui.QGridLayout(Form)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.valveGroupBox = QtGui.QGroupBox(Form)
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
        self.comboBox_2 = QtGui.QComboBox(self.valveGroupBox)
        self.comboBox_2.setObjectName(_fromUtf8("comboBox_2"))
        self.comboBox_2.addItem(_fromUtf8(""))
        self.comboBox_2.addItem(_fromUtf8(""))
        self.gridLayout_2.addWidget(self.comboBox_2, 2, 2, 2, 2)
        self.valveStatusLabel = QtGui.QLabel(self.valveGroupBox)
        font = QtGui.QFont()
        font.setPointSize(20)
        self.valveStatusLabel.setFont(font)
        self.valveStatusLabel.setObjectName(_fromUtf8("valveStatusLabel"))
        self.gridLayout_2.addWidget(self.valveStatusLabel, 0, 0, 1, 4)
        self.gridLayout.addWidget(self.valveGroupBox, 0, 0, 1, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)
        Form.setTabOrder(self.desiredPortComboBox, self.comboBox_2)
        Form.setTabOrder(self.comboBox_2, self.changePortButton)

    def retranslateUi(self, Form):
        Form.setWindowTitle(_translate("Form", "Form", None))
        self.valveGroupBox.setTitle(_translate("Form", "Valve 1", None))
        self.desiredPortLabel.setText(_translate("Form", "Desired Port", None))
        self.desiredPortComboBox.setItemText(0, _translate("Form", "Position", None))
        self.valveConfigurationLabel.setText(_translate("Form", "Valve Configuration", None))
        self.changePortButton.setText(_translate("Form", "Change Port", None))
        self.rotationDirectionLabel.setText(_translate("Form", "Rotation Direction", None))
        self.comboBox_2.setItemText(0, _translate("Form", "Clockwise", None))
        self.comboBox_2.setItemText(1, _translate("Form", "Counter Clockwise", None))
        self.valveStatusLabel.setText(_translate("Form", "Valve Status", None))

