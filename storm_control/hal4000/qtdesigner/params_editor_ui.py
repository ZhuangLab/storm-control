# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'params-editor.ui'
#
# Created: Wed Feb 24 09:37:44 2016
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
        Dialog.resize(845, 654)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        Dialog.setMinimumSize(QtCore.QSize(100, 100))
        Dialog.setMaximumSize(QtCore.QSize(10000, 10000))
        self.gridLayout = QtGui.QGridLayout(Dialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.editTabWidget = QtGui.QTabWidget(Dialog)
        self.editTabWidget.setObjectName(_fromUtf8("editTabWidget"))
        self.Main = QtGui.QWidget()
        self.Main.setObjectName(_fromUtf8("Main"))
        self.editTabWidget.addTab(self.Main, _fromUtf8(""))
        self.tab2 = QtGui.QWidget()
        self.tab2.setObjectName(_fromUtf8("tab2"))
        self.editTabWidget.addTab(self.tab2, _fromUtf8(""))
        self.verticalLayout.addWidget(self.editTabWidget)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.updateButton = QtGui.QPushButton(Dialog)
        self.updateButton.setObjectName(_fromUtf8("updateButton"))
        self.horizontalLayout.addWidget(self.updateButton)
        self.okButton = QtGui.QPushButton(Dialog)
        self.okButton.setObjectName(_fromUtf8("okButton"))
        self.horizontalLayout.addWidget(self.okButton)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.gridLayout.addLayout(self.verticalLayout, 1, 0, 1, 1)
        self.parametersNameLabel = QtGui.QLabel(Dialog)
        self.parametersNameLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.parametersNameLabel.setObjectName(_fromUtf8("parametersNameLabel"))
        self.gridLayout.addWidget(self.parametersNameLabel, 0, 0, 1, 1)

        self.retranslateUi(Dialog)
        self.editTabWidget.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "HAL-4000 Parameters Editor", None))
        self.editTabWidget.setTabText(self.editTabWidget.indexOf(self.Main), _translate("Dialog", "Main", None))
        self.editTabWidget.setTabText(self.editTabWidget.indexOf(self.tab2), _translate("Dialog", "Tab 2", None))
        self.updateButton.setText(_translate("Dialog", "Update", None))
        self.okButton.setText(_translate("Dialog", "Ok", None))
        self.parametersNameLabel.setText(_translate("Dialog", "NA", None))

