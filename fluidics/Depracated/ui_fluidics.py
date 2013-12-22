# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'fluidics.ui'
#
# Created: Fri Dec 20 10:19:24 2013
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
        MainWindow.resize(1283, 961)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.valveGroupBox = QtGui.QGroupBox(self.centralwidget)
        self.valveGroupBox.setGeometry(QtCore.QRect(290, 10, 461, 511))
        self.valveGroupBox.setObjectName(_fromUtf8("valveGroupBox"))
        self.gridLayout_2 = QtGui.QGridLayout(self.valveGroupBox)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.valveScrollArea = QtGui.QScrollArea(self.valveGroupBox)
        self.valveScrollArea.setWidgetResizable(True)
        self.valveScrollArea.setObjectName(_fromUtf8("valveScrollArea"))
        self.valveScrollAreaContents = QtGui.QWidget()
        self.valveScrollAreaContents.setGeometry(QtCore.QRect(0, 0, 439, 476))
        self.valveScrollAreaContents.setObjectName(_fromUtf8("valveScrollAreaContents"))
        self.valveScrollArea.setWidget(self.valveScrollAreaContents)
        self.gridLayout_2.addWidget(self.valveScrollArea, 0, 0, 1, 1)
        self.configurationBox = QtGui.QGroupBox(self.centralwidget)
        self.configurationBox.setGeometry(QtCore.QRect(10, 10, 276, 181))
        self.configurationBox.setObjectName(_fromUtf8("configurationBox"))
        self.gridLayout = QtGui.QGridLayout(self.configurationBox)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.executeConfigurationButton = QtGui.QPushButton(self.configurationBox)
        self.executeConfigurationButton.setObjectName(_fromUtf8("executeConfigurationButton"))
        self.gridLayout.addWidget(self.executeConfigurationButton, 1, 0, 1, 1)
        self.loadConfigurationButton = QtGui.QPushButton(self.configurationBox)
        self.loadConfigurationButton.setObjectName(_fromUtf8("loadConfigurationButton"))
        self.gridLayout.addWidget(self.loadConfigurationButton, 1, 1, 1, 1)
        self.configurationList = QtGui.QListWidget(self.configurationBox)
        self.configurationList.setObjectName(_fromUtf8("configurationList"))
        self.gridLayout.addWidget(self.configurationList, 0, 0, 1, 2)
        self.recipeBox = QtGui.QGroupBox(self.centralwidget)
        self.recipeBox.setGeometry(QtCore.QRect(10, 200, 276, 321))
        self.recipeBox.setObjectName(_fromUtf8("recipeBox"))
        self.recipeListBox = QtGui.QListWidget(self.recipeBox)
        self.recipeListBox.setGeometry(QtCore.QRect(10, 20, 256, 91))
        self.recipeListBox.setObjectName(_fromUtf8("recipeListBox"))
        self.loadRecipeButton = QtGui.QPushButton(self.recipeBox)
        self.loadRecipeButton.setGeometry(QtCore.QRect(190, 120, 75, 23))
        self.loadRecipeButton.setObjectName(_fromUtf8("loadRecipeButton"))
        self.tableWidget = QtGui.QTableWidget(self.recipeBox)
        self.tableWidget.setGeometry(QtCore.QRect(10, 150, 256, 111))
        self.tableWidget.setObjectName(_fromUtf8("tableWidget"))
        self.tableWidget.setColumnCount(2)
        self.tableWidget.setRowCount(0)
        item = QtGui.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, item)
        item = QtGui.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, item)
        self.executeRecipeButton = QtGui.QPushButton(self.recipeBox)
        self.executeRecipeButton.setGeometry(QtCore.QRect(10, 120, 75, 23))
        self.executeRecipeButton.setObjectName(_fromUtf8("executeRecipeButton"))
        self.elapsedTimeLabel = QtGui.QLabel(self.recipeBox)
        self.elapsedTimeLabel.setGeometry(QtCore.QRect(180, 260, 78, 16))
        self.elapsedTimeLabel.setObjectName(_fromUtf8("elapsedTimeLabel"))
        self.targetTimeLabel = QtGui.QLabel(self.recipeBox)
        self.targetTimeLabel.setGeometry(QtCore.QRect(20, 260, 72, 16))
        self.targetTimeLabel.setObjectName(_fromUtf8("targetTimeLabel"))
        self.elaspedTimeLCD = QtGui.QLCDNumber(self.recipeBox)
        self.elaspedTimeLCD.setGeometry(QtCore.QRect(180, 280, 64, 23))
        self.elaspedTimeLCD.setObjectName(_fromUtf8("elaspedTimeLCD"))
        self.targetTimeLCD = QtGui.QLCDNumber(self.recipeBox)
        self.targetTimeLCD.setGeometry(QtCore.QRect(20, 280, 64, 23))
        self.targetTimeLCD.setObjectName(_fromUtf8("targetTimeLCD"))
        self.stopRecipeButton = QtGui.QPushButton(self.recipeBox)
        self.stopRecipeButton.setGeometry(QtCore.QRect(100, 120, 75, 23))
        self.stopRecipeButton.setObjectName(_fromUtf8("stopRecipeButton"))
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1283, 21))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menuFile = QtGui.QMenu(self.menubar)
        self.menuFile.setObjectName(_fromUtf8("menuFile"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)
        self.actionQuit = QtGui.QAction(MainWindow)
        self.actionQuit.setObjectName(_fromUtf8("actionQuit"))
        self.actionLoadConfigurationXML = QtGui.QAction(MainWindow)
        self.actionLoadConfigurationXML.setObjectName(_fromUtf8("actionLoadConfigurationXML"))
        self.actionLoadRecipesXML = QtGui.QAction(MainWindow)
        self.actionLoadRecipesXML.setObjectName(_fromUtf8("actionLoadRecipesXML"))
        self.actionLoad_Recipe_Book = QtGui.QAction(MainWindow)
        self.actionLoad_Recipe_Book.setObjectName(_fromUtf8("actionLoad_Recipe_Book"))
        self.menuFile.addAction(self.actionQuit)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionLoadConfigurationXML)
        self.menuFile.addAction(self.actionLoadRecipesXML)
        self.menuFile.addAction(self.actionLoad_Recipe_Book)
        self.menubar.addAction(self.menuFile.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow", None))
        self.valveGroupBox.setTitle(_translate("MainWindow", "Valve Control and Status", None))
        self.configurationBox.setTitle(_translate("MainWindow", "Defined Configurations", None))
        self.executeConfigurationButton.setText(_translate("MainWindow", "Execute", None))
        self.loadConfigurationButton.setText(_translate("MainWindow", "Load", None))
        self.recipeBox.setTitle(_translate("MainWindow", "Recipe Books", None))
        self.loadRecipeButton.setText(_translate("MainWindow", "Load", None))
        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("MainWindow", "Configuration", None))
        item = self.tableWidget.horizontalHeaderItem(1)
        item.setText(_translate("MainWindow", "Duration (s)", None))
        self.executeRecipeButton.setText(_translate("MainWindow", "Execute", None))
        self.elapsedTimeLabel.setText(_translate("MainWindow", "Elapsed Time (s)", None))
        self.targetTimeLabel.setText(_translate("MainWindow", "Target Time (s)", None))
        self.stopRecipeButton.setText(_translate("MainWindow", "Stop", None))
        self.menuFile.setTitle(_translate("MainWindow", "File", None))
        self.actionQuit.setText(_translate("MainWindow", "Quit", None))
        self.actionLoadConfigurationXML.setText(_translate("MainWindow", "Load Valve Configuration", None))
        self.actionLoadRecipesXML.setText(_translate("MainWindow", "Load Configurations", None))
        self.actionLoad_Recipe_Book.setText(_translate("MainWindow", "Load Recipe Book", None))

