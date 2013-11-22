# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'lockdisplay.ui'
#
# Created: Fri Nov 22 08:34:09 2013
#      by: PyQt4 UI code generator 4.9.6
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
        Form.resize(298, 249)
        self.statusBox = QtGui.QGroupBox(Form)
        self.statusBox.setGeometry(QtCore.QRect(10, 0, 281, 241))
        self.statusBox.setObjectName(_fromUtf8("statusBox"))
        self.offsetFrame = QtGui.QFrame(self.statusBox)
        self.offsetFrame.setGeometry(QtCore.QRect(20, 40, 21, 161))
        self.offsetFrame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.offsetFrame.setFrameShadow(QtGui.QFrame.Sunken)
        self.offsetFrame.setObjectName(_fromUtf8("offsetFrame"))
        self.offsetLabel = QtGui.QLabel(self.statusBox)
        self.offsetLabel.setGeometry(QtCore.QRect(8, 20, 46, 14))
        self.offsetLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.offsetLabel.setObjectName(_fromUtf8("offsetLabel"))
        self.zFrame = QtGui.QFrame(self.statusBox)
        self.zFrame.setGeometry(QtCore.QRect(111, 40, 21, 161))
        self.zFrame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.zFrame.setFrameShadow(QtGui.QFrame.Sunken)
        self.zFrame.setObjectName(_fromUtf8("zFrame"))
        self.zLabel = QtGui.QLabel(self.statusBox)
        self.zLabel.setGeometry(QtCore.QRect(97, 20, 46, 14))
        self.zLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.zLabel.setObjectName(_fromUtf8("zLabel"))
        self.sumLabel = QtGui.QLabel(self.statusBox)
        self.sumLabel.setGeometry(QtCore.QRect(52, 20, 46, 14))
        self.sumLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.sumLabel.setObjectName(_fromUtf8("sumLabel"))
        self.sumFrame = QtGui.QFrame(self.statusBox)
        self.sumFrame.setGeometry(QtCore.QRect(65, 40, 21, 161))
        self.sumFrame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.sumFrame.setFrameShadow(QtGui.QFrame.Sunken)
        self.sumFrame.setObjectName(_fromUtf8("sumFrame"))
        self.offsetText = QtGui.QLabel(self.statusBox)
        self.offsetText.setGeometry(QtCore.QRect(10, 210, 46, 14))
        self.offsetText.setAlignment(QtCore.Qt.AlignCenter)
        self.offsetText.setObjectName(_fromUtf8("offsetText"))
        self.sumText = QtGui.QLabel(self.statusBox)
        self.sumText.setGeometry(QtCore.QRect(54, 210, 46, 14))
        self.sumText.setAlignment(QtCore.Qt.AlignCenter)
        self.sumText.setObjectName(_fromUtf8("sumText"))
        self.zText = QtGui.QLabel(self.statusBox)
        self.zText.setGeometry(QtCore.QRect(92, 209, 61, 16))
        self.zText.setAlignment(QtCore.Qt.AlignCenter)
        self.zText.setObjectName(_fromUtf8("zText"))
        self.qpdFrame = QtGui.QFrame(self.statusBox)
        self.qpdFrame.setGeometry(QtCore.QRect(146, 40, 120, 120))
        self.qpdFrame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.qpdFrame.setFrameShadow(QtGui.QFrame.Sunken)
        self.qpdFrame.setObjectName(_fromUtf8("qpdFrame"))
        self.qpdLabel = QtGui.QLabel(self.statusBox)
        self.qpdLabel.setGeometry(QtCore.QRect(170, 20, 71, 16))
        self.qpdLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.qpdLabel.setObjectName(_fromUtf8("qpdLabel"))
        self.qpdXText = QtGui.QLabel(self.statusBox)
        self.qpdXText.setGeometry(QtCore.QRect(153, 168, 46, 14))
        self.qpdXText.setObjectName(_fromUtf8("qpdXText"))
        self.qpdYText = QtGui.QLabel(self.statusBox)
        self.qpdYText.setGeometry(QtCore.QRect(213, 168, 46, 14))
        self.qpdYText.setObjectName(_fromUtf8("qpdYText"))
        self.irButton = QtGui.QPushButton(self.statusBox)
        self.irButton.setGeometry(QtCore.QRect(211, 210, 61, 24))
        self.irButton.setObjectName(_fromUtf8("irButton"))
        self.irSlider = QtGui.QSlider(self.statusBox)
        self.irSlider.setGeometry(QtCore.QRect(155, 189, 101, 19))
        self.irSlider.setMinimum(0)
        self.irSlider.setMaximum(100)
        self.irSlider.setProperty("value", 0)
        self.irSlider.setOrientation(QtCore.Qt.Horizontal)
        self.irSlider.setObjectName(_fromUtf8("irSlider"))

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(_translate("Form", "Form", None))
        self.statusBox.setTitle(_translate("Form", "Status", None))
        self.offsetLabel.setText(_translate("Form", "Offset", None))
        self.zLabel.setText(_translate("Form", "Stage Z", None))
        self.sumLabel.setText(_translate("Form", "Sum", None))
        self.offsetText.setText(_translate("Form", "TextLabel", None))
        self.sumText.setText(_translate("Form", "TextLabel", None))
        self.zText.setText(_translate("Form", "TextLabel", None))
        self.qpdLabel.setText(_translate("Form", "QPD Signal", None))
        self.qpdXText.setText(_translate("Form", "x:", None))
        self.qpdYText.setText(_translate("Form", "y:", None))
        self.irButton.setText(_translate("Form", "IR ON", None))

