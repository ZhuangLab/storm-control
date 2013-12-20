#
# Widget that provides an interface to the the control and status of a single
# Hamilton MVP
#
# Jeff Moffitt
# jeffmoffitt@gmail.com
# December 20, 2013
#

import os
import sys
from PyQt4 import QtCore, QtGui

## QValveControl
#
# This class creates and handles interaction with the controls that
# describe a single Hamilton MVP
#
class QValveControl(QtGui.QWidget):
    move_valve_signal = QtCore.pyqtSignal(int)

    ## __init__
    #
    # @param parent (Optional) the PyQt parent of this object.
    #
    def __init__(self, valve_ID, port_configuration, parent = None):
        QtGui.QWidget.__init__(self, parent)

        # Set internal variables
        self.valve_ID = valve_ID
        self.numPositions = -1
        
        # Initialize layout
        self.layout = QtGui.QHBoxLayout(self)

        # Define Status Label
        self.statusLabel = QtGui.QLabel()
        self.statusLabel.setObjectName("Status_Label")
        self.statusLabel.setText("Uninitialized")
        font = QtGui.QFont()
        font.setPointSize(20)
        self.statusLabel.setFont(font)

        # Define Valve Position Combo Box
        self.desiredPosition = QtGui.QComboBox()
        self.desiredPosition.setObjectName("Desired_Valve_Position")
        for label in self.getDefaultPositionNames(port_configuration):
            self.desiredPosition.addItem(label)
        
        # Define Rotation Direction Combo Box
        self.desiredRotation = QtGui.QComboBox()
        self.desiredRotation.addItem("Clockwise")
        self.desiredRotation.addItem("Counter Clockwise")
        self.setObjectName("Desired_Rotation_Direction")

        # Define Push Button
        self.moveValveButton = QtGui.QPushButton("Move Valve")
        self.moveValveButton.setObjectName("Move_Valve_Button")

        # Connect Move Valve Button
        self.moveValveButton.clicked.connect(self.MoveValvePressed)

        # Add widgets
        self.layout.addWidget(self.statusLabel)
        self.layout.addWidget(self.desiredPosition)
        self.layout.addWidget(self.desiredRotation)
        self.layout.addWidget(self.moveValveButton)

    ## setValveID
    #
    # @param parent (Optional) the PyQt parent of this object.
    #
    def setValveID(self, valve_ID = 0):
        self.valve_ID = valve_ID

    ## Create Default Position Names
    def getDefaultPositionNames(self, port_configuration)
        return {"8 ports": ("Position 1", "Position 2", "Position 3", "Position 4"
                            "Position 5", "Position 6", "Position 7", "Position 8"),
                "6 ports": ("Position 1", "Position 2", "Position 3", "Position 4"
                            "Position 5", "Position 6"),
                "3 ports": ("Position 1", "Position 2", "Position 3"),
                "2 ports @180": ("Position 1", "Position 2"),
                "2 ports @90": ("Position 1", "Position 2"),
                "4 ports": ("Position 1", "Position 2", "Position 3", "Position 4")
                }.get(port_configuration, "Unknown")

    ## Set Valve Position Names in Combo Box
    def setPositionNames(self, positionNames = ("Uninitialized")):

        #Remove Existing Items
        self.desiredPosition.clear()

        # Add new items
        for positionName in positionNames:
            self.desiredPosition.addItem(positionName)

        self.numPositions = self.desiredPosition.count()

    ## Move Valve Pressed
    def moveValveButtonPressed(self):
        self.move_valve_signal.emit(self.valveID) # Send PyQt Signal
    
    ## UpdateStatus
    def updateValveStatus(self, valveStatusTuple = (0, False)):
        # valveStatusTuple = (valveID, isMoving?)

        # Update valve position
        statusText = self.desiredPosition.itemText(valveStatusTuple[0])
        self.statusLabel.setText(statusText)
        
        # Update valve move status
        if valveStatusTuple[1]:
            self.statusLabel.setStyleSheet("QLabel { color: black}")
        else:
            self.statusLabel.setStyleSheet("QLabel { color: red}")

#
# The MIT License
#
# Copyright (c) 2012 Zhuang Lab, Harvard University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

