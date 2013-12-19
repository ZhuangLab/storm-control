# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'simple_fluidics.ui'
#
# Created: Thu Dec 19 14:55:10 2013
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

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(300, 199)
        self.centralwidget = QtGui.QWidget(MainWindow)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.gridLayout = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        spacerItem = QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 5, 2, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem1, 8, 0, 1, 1)
        self.currentValveStatus = QtGui.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(20)
        self.currentValveStatus.setFont(font)
        self.currentValveStatus.setObjectName(_fromUtf8("currentValveStatus"))
        self.gridLayout.addWidget(self.currentValveStatus, 0, 0, 1, 1)
        self.desiredValvePosition = QtGui.QComboBox(self.centralwidget)
        self.desiredValvePosition.setObjectName(_fromUtf8("desiredValvePosition"))
        self.desiredValvePosition.addItem(_fromUtf8(""))
        self.desiredValvePosition.addItem(_fromUtf8(""))
        self.desiredValvePosition.addItem(_fromUtf8(""))
        self.desiredValvePosition.addItem(_fromUtf8(""))
        self.desiredValvePosition.addItem(_fromUtf8(""))
        self.desiredValvePosition.addItem(_fromUtf8(""))
        self.desiredValvePosition.addItem(_fromUtf8(""))
        self.desiredValvePosition.addItem(_fromUtf8(""))
        self.gridLayout.addWidget(self.desiredValvePosition, 5, 0, 1, 1)
        self.desiredRotationDirection = QtGui.QComboBox(self.centralwidget)
        self.desiredRotationDirection.setObjectName(_fromUtf8("desiredRotationDirection"))
        self.desiredRotationDirection.addItem(_fromUtf8(""))
        self.desiredRotationDirection.addItem(_fromUtf8(""))
        self.gridLayout.addWidget(self.desiredRotationDirection, 6, 0, 1, 1)
        self.label_2 = QtGui.QLabel(self.centralwidget)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 5, 1, 1, 1)
        self.label_3 = QtGui.QLabel(self.centralwidget)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.gridLayout.addWidget(self.label_3, 6, 1, 1, 1)
        self.changeValvePosition = QtGui.QPushButton(self.centralwidget)
        self.changeValvePosition.setMinimumSize(QtCore.QSize(100, 0))
        self.changeValvePosition.setObjectName(_fromUtf8("changeValvePosition"))
        self.gridLayout.addWidget(self.changeValvePosition, 7, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 300, 21))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menuFile = QtGui.QMenu(self.menubar)
        self.menuFile.setObjectName(_fromUtf8("menuFile"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)
        self.actionQuit = QtGui.QAction(MainWindow)
        self.actionQuit.setObjectName(_fromUtf8("actionQuit"))
        self.actionInitializeHamilton = QtGui.QAction(MainWindow)
        self.actionInitializeHamilton.setObjectName(_fromUtf8("actionInitializeHamilton"))
        self.actionReaddressHamilton = QtGui.QAction(MainWindow)
        self.actionReaddressHamilton.setObjectName(_fromUtf8("actionReaddressHamilton"))
        self.menuFile.addAction(self.actionQuit)
        self.menuFile.addAction(self.actionInitializeHamilton)
        self.menubar.addAction(self.menuFile.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow", None))
        self.currentValveStatus.setText(_translate("MainWindow", "Valve Position", None))
        self.desiredValvePosition.setItemText(0, _translate("MainWindow", "Position 1", None))
        self.desiredValvePosition.setItemText(1, _translate("MainWindow", "Position 2", None))
        self.desiredValvePosition.setItemText(2, _translate("MainWindow", "Position 3", None))
        self.desiredValvePosition.setItemText(3, _translate("MainWindow", "Position 4", None))
        self.desiredValvePosition.setItemText(4, _translate("MainWindow", "Position 5", None))
        self.desiredValvePosition.setItemText(5, _translate("MainWindow", "Position 6", None))
        self.desiredValvePosition.setItemText(6, _translate("MainWindow", "Position 7", None))
        self.desiredValvePosition.setItemText(7, _translate("MainWindow", "Position 8", None))
        self.desiredRotationDirection.setItemText(0, _translate("MainWindow", "Clockwise", None))
        self.desiredRotationDirection.setItemText(1, _translate("MainWindow", "Counter Clockwise", None))
        self.label_2.setText(_translate("MainWindow", "New Valve Position", None))
        self.label_3.setText(_translate("MainWindow", "Direction", None))
        self.changeValvePosition.setText(_translate("MainWindow", "Change Position", None))
        self.menuFile.setTitle(_translate("MainWindow", "File", None))
        self.actionQuit.setText(_translate("MainWindow", "Quit", None))
        self.actionInitializeHamilton.setText(_translate("MainWindow", "Initialize Hamilton", None))
        self.actionReaddressHamilton.setText(_translate("MainWindow", "Readdress Hamilton", None))

