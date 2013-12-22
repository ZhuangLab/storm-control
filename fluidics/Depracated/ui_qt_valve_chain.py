# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'qt_valve_chain.ui'
#
# Created: Sat Dec 21 15:51:04 2013
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
        Form.resize(584, 398)
        self.verticalLayout = QtGui.QVBoxLayout(Form)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.valveChainAreaLabel = QtGui.QLabel(Form)
        self.valveChainAreaLabel.setObjectName(_fromUtf8("valveChainAreaLabel"))
        self.verticalLayout.addWidget(self.valveChainAreaLabel)
        self.valveChainScrollArea = QtGui.QScrollArea(Form)
        self.valveChainScrollArea.setWidgetResizable(True)
        self.valveChainScrollArea.setObjectName(_fromUtf8("valveChainScrollArea"))
        self.scrollAreaWidgetContents = QtGui.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 564, 359))
        self.scrollAreaWidgetContents.setObjectName(_fromUtf8("scrollAreaWidgetContents"))
        self.valveChainScrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout.addWidget(self.valveChainScrollArea)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(_translate("Form", "Form", None))
        self.valveChainAreaLabel.setText(_translate("Form", "Valves", None))

