# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'fluidics.ui'
#
# Created: Thu Dec 19 11:29:34 2013
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
        MainWindow.resize(131, 289)
        self.centralwidget = QtGui.QWidget(MainWindow)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.gridLayout = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        spacerItem = QtGui.QSpacerItem(20, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 8, 0, 1, 1)
        self.pos3RadioButton = QtGui.QRadioButton(self.centralwidget)
        self.pos3RadioButton.setObjectName(_fromUtf8("pos3RadioButton"))
        self.gridLayout.addWidget(self.pos3RadioButton, 0, 0, 1, 1)
        self.pos2RadioButton = QtGui.QRadioButton(self.centralwidget)
        self.pos2RadioButton.setObjectName(_fromUtf8("pos2RadioButton"))
        self.gridLayout.addWidget(self.pos2RadioButton, 2, 0, 1, 1)
        self.pos1RadioButton = QtGui.QRadioButton(self.centralwidget)
        self.pos1RadioButton.setObjectName(_fromUtf8("pos1RadioButton"))
        self.gridLayout.addWidget(self.pos1RadioButton, 1, 0, 1, 1)
        self.pos6RadioButton = QtGui.QRadioButton(self.centralwidget)
        self.pos6RadioButton.setObjectName(_fromUtf8("pos6RadioButton"))
        self.gridLayout.addWidget(self.pos6RadioButton, 5, 0, 1, 1)
        self.pos7RadioButton = QtGui.QRadioButton(self.centralwidget)
        self.pos7RadioButton.setObjectName(_fromUtf8("pos7RadioButton"))
        self.gridLayout.addWidget(self.pos7RadioButton, 6, 0, 1, 1)
        self.pos5RadioButton = QtGui.QRadioButton(self.centralwidget)
        self.pos5RadioButton.setObjectName(_fromUtf8("pos5RadioButton"))
        self.gridLayout.addWidget(self.pos5RadioButton, 4, 0, 1, 1)
        self.pos4RadioButton = QtGui.QRadioButton(self.centralwidget)
        self.pos4RadioButton.setMinimumSize(QtCore.QSize(0, 0))
        self.pos4RadioButton.setObjectName(_fromUtf8("pos4RadioButton"))
        self.gridLayout.addWidget(self.pos4RadioButton, 3, 0, 1, 1)
        self.pos8RadioButton = QtGui.QRadioButton(self.centralwidget)
        self.pos8RadioButton.setObjectName(_fromUtf8("pos8RadioButton"))
        self.gridLayout.addWidget(self.pos8RadioButton, 7, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 131, 21))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menuFile = QtGui.QMenu(self.menubar)
        self.menuFile.setObjectName(_fromUtf8("menuFile"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)
        self.actionQuit = QtGui.QAction(MainWindow)
        self.actionQuit.setObjectName(_fromUtf8("actionQuit"))
        self.menuFile.addAction(self.actionQuit)
        self.menubar.addAction(self.menuFile.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow", None))
        self.pos3RadioButton.setText(_translate("MainWindow", "1", None))
        self.pos2RadioButton.setText(_translate("MainWindow", "3", None))
        self.pos1RadioButton.setText(_translate("MainWindow", "2", None))
        self.pos6RadioButton.setText(_translate("MainWindow", "6", None))
        self.pos7RadioButton.setText(_translate("MainWindow", "7", None))
        self.pos5RadioButton.setText(_translate("MainWindow", "5", None))
        self.pos4RadioButton.setText(_translate("MainWindow", "4", None))
        self.pos8RadioButton.setText(_translate("MainWindow", "8", None))
        self.menuFile.setTitle(_translate("MainWindow", "File", None))
        self.actionQuit.setText(_translate("MainWindow", "Quit", None))

