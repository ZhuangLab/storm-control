# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'qt_regex_file_dialog.ui'
#
# Created: Mon Jun 15 14:41:58 2015
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

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(655, 468)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        self.verticalLayout = QtGui.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.nameLabel = QtGui.QLabel(Dialog)
        self.nameLabel.setObjectName(_fromUtf8("nameLabel"))
        self.horizontalLayout.addWidget(self.nameLabel)
        self.nameLineEdit = QtGui.QLineEdit(Dialog)
        self.nameLineEdit.setObjectName(_fromUtf8("nameLineEdit"))
        self.horizontalLayout.addWidget(self.nameLineEdit)
        self.frameNumLabel = QtGui.QLabel(Dialog)
        self.frameNumLabel.setObjectName(_fromUtf8("frameNumLabel"))
        self.horizontalLayout.addWidget(self.frameNumLabel)
        self.frameNumSpinBox = QtGui.QSpinBox(Dialog)
        self.frameNumSpinBox.setObjectName(_fromUtf8("frameNumSpinBox"))
        self.horizontalLayout.addWidget(self.frameNumSpinBox)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Dialog", None))
        self.nameLabel.setText(_translate("Dialog", "Name Filter:", None))
        self.frameNumLabel.setText(_translate("Dialog", "Frame Number:", None))

