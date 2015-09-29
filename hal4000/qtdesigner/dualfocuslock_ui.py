# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dualfocuslock.ui'
#
# Created: Fri Jul 24 12:06:08 2015
#      by: PyQt4 UI code generator 4.11.3
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

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(811, 310)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        Dialog.setMinimumSize(QtCore.QSize(811, 310))
        Dialog.setMaximumSize(QtCore.QSize(811, 310))
        self.focusLockBox = QtGui.QGroupBox(Dialog)
        self.focusLockBox.setGeometry(QtCore.QRect(10, 0, 792, 271))
        self.focusLockBox.setObjectName(_fromUtf8("focusLockBox"))
        self.modeBox = QtGui.QGroupBox(self.focusLockBox)
        self.modeBox.setGeometry(QtCore.QRect(10, 20, 181, 151))
        self.modeBox.setObjectName(_fromUtf8("modeBox"))
        self.lockButton = QtGui.QPushButton(self.modeBox)
        self.lockButton.setGeometry(QtCore.QRect(110, 90, 61, 24))
        self.lockButton.setObjectName(_fromUtf8("lockButton"))
        self.lockLabel = QtGui.QLabel(self.modeBox)
        self.lockLabel.setGeometry(QtCore.QRect(117, 30, 46, 14))
        self.lockLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.lockLabel.setObjectName(_fromUtf8("lockLabel"))
        self.modeWidget = QtGui.QWidget(self.modeBox)
        self.modeWidget.setGeometry(QtCore.QRect(7, 12, 101, 131))
        self.modeWidget.setObjectName(_fromUtf8("modeWidget"))
        self.jumpControlBox = QtGui.QGroupBox(self.focusLockBox)
        self.jumpControlBox.setGeometry(QtCore.QRect(10, 180, 181, 81))
        self.jumpControlBox.setObjectName(_fromUtf8("jumpControlBox"))
        self.jumpLabel = QtGui.QLabel(self.jumpControlBox)
        self.jumpLabel.setGeometry(QtCore.QRect(104, 22, 61, 16))
        self.jumpLabel.setObjectName(_fromUtf8("jumpLabel"))
        self.jumpSpinBox = QtGui.QDoubleSpinBox(self.jumpControlBox)
        self.jumpSpinBox.setGeometry(QtCore.QRect(10, 20, 91, 22))
        self.jumpSpinBox.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.jumpSpinBox.setMinimum(-10.0)
        self.jumpSpinBox.setMaximum(10.0)
        self.jumpSpinBox.setSingleStep(0.01)
        self.jumpSpinBox.setObjectName(_fromUtf8("jumpSpinBox"))
        self.jumpPButton = QtGui.QPushButton(self.jumpControlBox)
        self.jumpPButton.setGeometry(QtCore.QRect(10, 50, 75, 24))
        self.jumpPButton.setObjectName(_fromUtf8("jumpPButton"))
        self.jumpNButton = QtGui.QPushButton(self.jumpControlBox)
        self.jumpNButton.setGeometry(QtCore.QRect(100, 50, 75, 24))
        self.jumpNButton.setObjectName(_fromUtf8("jumpNButton"))
        self.lockDisplay1Widget = QtGui.QWidget(self.focusLockBox)
        self.lockDisplay1Widget.setGeometry(QtCore.QRect(193, 20, 298, 249))
        self.lockDisplay1Widget.setObjectName(_fromUtf8("lockDisplay1Widget"))
        self.lockDisplay2Widget = QtGui.QWidget(self.focusLockBox)
        self.lockDisplay2Widget.setGeometry(QtCore.QRect(494, 20, 298, 249))
        self.lockDisplay2Widget.setObjectName(_fromUtf8("lockDisplay2Widget"))
        self.okButton = QtGui.QPushButton(Dialog)
        self.okButton.setGeometry(QtCore.QRect(730, 280, 75, 24))
        self.okButton.setObjectName(_fromUtf8("okButton"))

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "HAL-4000 Focus Lock", None))
        self.focusLockBox.setTitle(_translate("Dialog", "Focus Lock Control", None))
        self.modeBox.setTitle(_translate("Dialog", "Mode", None))
        self.lockButton.setText(_translate("Dialog", "Lock", None))
        self.lockLabel.setText(_translate("Dialog", "Locked", None))
        self.jumpControlBox.setTitle(_translate("Dialog", "Jump Control", None))
        self.jumpLabel.setText(_translate("Dialog", "Offset (um)", None))
        self.jumpPButton.setText(_translate("Dialog", "Jump (+)", None))
        self.jumpNButton.setText(_translate("Dialog", "Jump (-)", None))
        self.okButton.setText(_translate("Dialog", "Ok", None))

