# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'loaddax_dialog.ui'
#
# Created: Sun May 24 13:21:55 2015
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

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(340, 137)
        self.gridLayout = QtGui.QGridLayout(Dialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.buttonBox = QtGui.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 5, 0, 1, 1)
        self.directory_line_edit = QtGui.QLineEdit(Dialog)
        self.directory_line_edit.setObjectName(_fromUtf8("directory_line_edit"))
        self.gridLayout.addWidget(self.directory_line_edit, 1, 0, 1, 1)
        self.directory_label = QtGui.QLabel(Dialog)
        self.directory_label.setObjectName(_fromUtf8("directory_label"))
        self.gridLayout.addWidget(self.directory_label, 0, 0, 1, 1)
        self.filter_label = QtGui.QLabel(Dialog)
        self.filter_label.setObjectName(_fromUtf8("filter_label"))
        self.gridLayout.addWidget(self.filter_label, 2, 0, 1, 1)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 6, 0, 1, 1)
        self.new_directory_button = QtGui.QPushButton(Dialog)
        self.new_directory_button.setObjectName(_fromUtf8("new_directory_button"))
        self.gridLayout.addWidget(self.new_directory_button, 1, 1, 1, 1)
        self.file_filter_line_edit = QtGui.QLineEdit(Dialog)
        self.file_filter_line_edit.setObjectName(_fromUtf8("file_filter_line_edit"))
        self.gridLayout.addWidget(self.file_filter_line_edit, 3, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), Dialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Dialog", None))
        self.directory_label.setText(_translate("Dialog", "Directory", None))
        self.filter_label.setText(_translate("Dialog", "File Name Filter", None))
        self.new_directory_button.setText(_translate("Dialog", "New Directory", None))

