# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'spotcounter.ui'
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

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(561, 640)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        Dialog.setMinimumSize(QtCore.QSize(561, 640))
        Dialog.setMaximumSize(QtCore.QSize(561, 640))
        self.okButton = QtGui.QPushButton(Dialog)
        self.okButton.setGeometry(QtCore.QRect(480, 610, 75, 24))
        self.okButton.setObjectName(_fromUtf8("okButton"))
        self.tabWidget = QtGui.QTabWidget(Dialog)
        self.tabWidget.setGeometry(QtCore.QRect(10, 10, 541, 591))
        self.tabWidget.setObjectName(_fromUtf8("tabWidget"))
        self.countsTab = QtGui.QWidget()
        self.countsTab.setObjectName(_fromUtf8("countsTab"))
        self.graphFrame = QtGui.QFrame(self.countsTab)
        self.graphFrame.setGeometry(QtCore.QRect(60, 40, 471, 371))
        self.graphFrame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.graphFrame.setFrameShadow(QtGui.QFrame.Sunken)
        self.graphFrame.setObjectName(_fromUtf8("graphFrame"))
        self.countsText1 = QtGui.QLabel(self.countsTab)
        self.countsText1.setGeometry(QtCore.QRect(20, 10, 101, 16))
        self.countsText1.setObjectName(_fromUtf8("countsText1"))
        self.countsLabel1 = QtGui.QLabel(self.countsTab)
        self.countsLabel1.setGeometry(QtCore.QRect(130, 10, 61, 16))
        self.countsLabel1.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.countsLabel1.setObjectName(_fromUtf8("countsLabel1"))
        self.label = QtGui.QLabel(self.countsTab)
        self.label.setGeometry(QtCore.QRect(100, 480, 341, 20))
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName(_fromUtf8("label"))
        self.minSpinBox = QtGui.QSpinBox(self.countsTab)
        self.minSpinBox.setGeometry(QtCore.QRect(5, 400, 51, 22))
        self.minSpinBox.setMaximum(1000)
        self.minSpinBox.setSingleStep(10)
        self.minSpinBox.setObjectName(_fromUtf8("minSpinBox"))
        self.maxSpinBox = QtGui.QSpinBox(self.countsTab)
        self.maxSpinBox.setGeometry(QtCore.QRect(5, 30, 51, 22))
        self.maxSpinBox.setMinimum(10)
        self.maxSpinBox.setMaximum(1000)
        self.maxSpinBox.setSingleStep(10)
        self.maxSpinBox.setProperty("value", 1000)
        self.maxSpinBox.setObjectName(_fromUtf8("maxSpinBox"))
        self.tabWidget.addTab(self.countsTab, _fromUtf8(""))
        self.imageTab = QtGui.QWidget()
        self.imageTab.setObjectName(_fromUtf8("imageTab"))
        self.imageFrame = QtGui.QFrame(self.imageTab)
        self.imageFrame.setGeometry(QtCore.QRect(10, 40, 516, 516))
        self.imageFrame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.imageFrame.setFrameShadow(QtGui.QFrame.Sunken)
        self.imageFrame.setObjectName(_fromUtf8("imageFrame"))
        self.countsText2 = QtGui.QLabel(self.imageTab)
        self.countsText2.setGeometry(QtCore.QRect(20, 10, 101, 16))
        self.countsText2.setObjectName(_fromUtf8("countsText2"))
        self.countsLabel2 = QtGui.QLabel(self.imageTab)
        self.countsLabel2.setGeometry(QtCore.QRect(130, 10, 61, 16))
        self.countsLabel2.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.countsLabel2.setObjectName(_fromUtf8("countsLabel2"))
        self.tabWidget.addTab(self.imageTab, _fromUtf8(""))

        self.retranslateUi(Dialog)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "HAL-4000 Spot Counter", None))
        self.okButton.setText(_translate("Dialog", "Ok", None))
        self.countsText1.setText(_translate("Dialog", "Total Localizations:", None))
        self.countsLabel1.setText(_translate("Dialog", "TextLabel", None))
        self.label.setText(_translate("Dialog", "This Space Intentionally Left Blank", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.countsTab), _translate("Dialog", "Counts", None))
        self.countsText2.setText(_translate("Dialog", "Total Localizations:", None))
        self.countsLabel2.setText(_translate("Dialog", "TextLabel", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.imageTab), _translate("Dialog", "STORM Image", None))

