#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
ZetCode PyQt4 tutorial 

In this example, we create a custom widget.

author: Jan Bodnar
website: zetcode.com 
last edited: October 2011
"""

import sys
from PyQt4 import QtGui, QtCore

class Main(QtGui.QMainWindow):
    def __init__(self, parent = None):
        super(Main, self).__init__(parent)

        # scroll area widget contents - layout
        self.scrollLayout = QtGui.QFormLayout()

        # scroll area widget contents
        self.scrollWidget = QtGui.QWidget()
        self.scrollWidget.setLayout(self.scrollLayout)

        # scroll area
        self.scrollArea = QtGui.QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.scrollWidget)

        # main layout
        self.mainLayout = QtGui.QVBoxLayout()

        # add all main to the main vLayout
        self.mainLayout.addWidget(self.scrollArea)

        self.valveCount = 1

        self.statusLabels = []
        self.desiredPositions = []
        self.desiredRotations = []
        self.valveButtons = []
        self.valveControlIDs = []
        
        for i in range(3):
            self.addValveControl(i)
        
        # central widget
        self.centralWidget = QtGui.QWidget()
        self.centralWidget.setLayout(self.mainLayout)

        # set central widget
        self.setCentralWidget(self.centralWidget)
        
    def addValveControl(self, ID):
        # Archive Control ID
        self.valveControlIDs.append(ID)
        
        # Define Status Label
        self.statusLabels.append(QtGui.QLabel())
        self.statusLabels[-1].setObjectName("valveStatusLabel_" + str(ID))
        self.statusLabels[-1].setText("Position " + str(ID))
        font = QtGui.QFont()
        font.setPointSize(20)
        self.statusLabels[-1].setFont(font)

        # Define Valve Position Combo Box
        self.desiredPositions.append(QtGui.QComboBox())
        self.desiredPositions[-1].addItem("Position 1")
        self.desiredPositions[-1].setObjectName("desiredValvePosition_" + str(ID))
        
        # Define Rotation Direction Combo Box
        self.desiredRotations.append(QtGui.QComboBox())
        self.desiredRotations[-1].setObjectName("desiredRotationDirection_" + str(ID))
        self.desiredRotations[-1].addItem("Clockwise")
        self.desiredRotations[-1].addItem("Counter Clockwise")

        # Define Push Button
        self.valveButtons.append(QtGui.QPushButton("Move Valve"))
        self.valveButtons[-1].setObjectName("valveMoveButton_" + str(ID))

        slotLambda = lambda: self.valveMoveButtonCurrentIndex_lambda(ID)
        self.valveButtons[-1].clicked.connect(slotLambda)

        layout = QtGui.QHBoxLayout()
        layout.addWidget(self.statusLabels[-1])
        layout.addWidget(self.desiredPositions[-1])
        layout.addWidget(self.desiredRotations[-1])
        layout.addWidget(self.valveButtons[-1])
        layout.addStretch(1)
        
        self.scrollLayout.addRow(layout)

    @QtCore.pyqtSlot(int)
    def valveMoveButtonCurrentIndex_lambda(self, int):
        print "Issued Move from Index: " + str(int)
        currentRotationIndex = self.desiredRotations[int].currentIndex()
        print "Found Rotation Index: " + str(currentRotationIndex)
        
    def IssueMoveCommand(self):
        print "Issued Move Command From: " + str(self.sender())
        
class MultiplePushButton(QtGui.QWidget):
    def __init__(self, parent=None):
        super(MultiplePushButton, self).__init__(parent)

        self.pushButton1 = QtGui.QPushButton("Button 1")
        self.pushButton2 = QtGui.QPushButton("Button 2")
        
        layout = QtGui.QHBoxLayout()
        layout.addWidget(self.pushButton1)
        layout.addWidget(self.pushButton2)
        self.setLayout(layout)

app = QtGui.QApplication(sys.argv)
myWidget = Main()
myWidget.show()
app.exec_()
