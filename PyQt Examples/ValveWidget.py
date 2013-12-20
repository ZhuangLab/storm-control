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

        # main button
        self.addButton = QtGui.QPushButton('button to add other widgets')
        self.addButton.clicked.connect(self.addWidget)

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
        self.mainLayout.addWidget(self.addButton)
        self.mainLayout.addWidget(self.scrollArea)

        # central widget
        self.centralWidget = QtGui.QWidget()
        self.centralWidget.setLayout(self.mainLayout)

        # set central widget
        self.setCentralWidget(self.centralWidget)

    def addWidget(self):
        self.scrollLayout.addRow(ValveControl())

class ValveControl(QtGui.QWidget):
    def __init__(self, parent=None):
        super(ValveControl, self).__init__(parent)

        # Create Box
        self.widgetBox = QtGui.QGroupBox()
        self.widgetBox.setObjectName("valve1Box")
        self.widgetBox.setGeometry(QtCore.QRect(10, 360, 163, 185) )

        # Define Status Label
        self.valveStatusLabel = QtGui.QLabel()
        self.valveStatusLabel.setObjectName("valveStatusLabel")
        self.valveStatusLabel.setText("Undefined")
        font = QtGui.QFont()
        font.setPointSize(20)
        self.valveStatusLabel.setFont(font)

        # Define Valve Position Combo Box
        self.desiredValvePosition = QtGui.QComboBox()
        self.desiredValvePosition.addItem("Position 1")
        
        # Rotation Direction
        self.desiredRotationDirection = QtGui.QComboBox()
        self.desiredRotationDirection.setObjectName("desiredRotationDirection")
        self.desiredRotationDirection.addItem("Clockwise")
        self.desiredRotationDirection.addItem("Counter Clockwise")

        # Define Push Button
        self.valveMoveButton = QtGui.QPushButton("Move Valve")

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.valveStatusLabel)
        layout.addWidget(self.desiredValvePosition)
        layout.addWidget(self.desiredRotationDirection)
        layout.addWidget(self.valveMoveButton)
        
        self.setLayout(layout)
        
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
