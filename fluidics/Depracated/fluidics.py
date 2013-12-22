#!/usr/bin/python

import os
import sys
import time
import hamilton
from PyQt4 import QtCore, QtGui

import ui_fluidics as fluidicsUi

#
# Main window
#
class Window(QtGui.QMainWindow):
    def __init__(self, parent = None):
        QtGui.QMainWindow.__init__(self, parent)

        # Define timer for periodic polling of valve status
        self.valve_poll_timer = QtCore.QTimer()        
        self.valve_poll_timer.setInterval(1000)
        #self.valve_poll_timer.timeout.connect(self.PollValveStatus)

         # ui setup
        self.ui = fluidicsUi.Ui_MainWindow()
        self.ui.setupUi(self)

        # Initialize hamilton class
        self.hamilton = hamilton.HamiltonMVP(verbose = False)

        # Add valve widgets based on the number of valves
        self.ui.statusLabels = []
        self.ui.desiredPositions = []
        self.ui.desiredRotations = []
        self.ui.valveButtons = []
        self.ui.valveControlIDs = []
        for i in range(self.hamilton.numDevices):
            self.addValveControl(i)

        # Connect Pull Down Menu Items: File
        self.ui.actionQuit.triggered.connect(self.Quit)

        # Create Layout for scroll widget
        self.ui.scrollLayout = QtGui.QFormLayout()
        self.valveScrollArea.setLayout(self.ui.scrollLayout)
        
    def addValveControl(self, ID):
        # Archive Control ID
        self.ui.valveControlIDs.append(ID)
        
        # Define Status Label
        self.ui.statusLabels.append(QtGui.QLabel())
        self.ui.statusLabels[-1].setObjectName("valveStatusLabel_" + str(ID))
        self.ui.statusLabels[-1].setText("Position " + str(ID))
        font = QtGui.QFont()
        font.setPointSize(20)
        self.ui.statusLabels[-1].setFont(font)

        # Define Valve Position Combo Box
        self.ui.desiredPositions.append(QtGui.QComboBox())
        self.ui.desiredPositions[-1].addItem("Position 1")
        self.ui.desiredPositions[-1].setObjectName("desiredValvePosition_" + str(ID))
        
        # Define Rotation Direction Combo Box
        self.ui.desiredRotations.append(QtGui.QComboBox())
        self.ui.desiredRotations[-1].setObjectName("desiredRotationDirection_" + str(ID))
        self.ui.desiredRotations[-1].addItem("Clockwise")
        self.ui.desiredRotations[-1].addItem("Counter Clockwise")

        # Define Push Button
        self.ui.valveButtons.append(QtGui.QPushButton("Move Valve"))
        self.ui.valveButtons[-1].setObjectName("valveMoveButton_" + str(ID))

        slotLambda = lambda: self.ui.valveMoveButtonCurrentIndex_lambda(ID)
        self.ui.valveButtons[-1].clicked.connect(slotLambda)

        layout = QtGui.QHBoxLayout()
        layout.addWidget(self.ui.statusLabels[-1])
        layout.addWidget(self.ui.desiredPositions[-1])
        layout.addWidget(self.ui.desiredRotations[-1])
        layout.addWidget(self.ui.valveButtons[-1])
        layout.addStretch(1)
        
        self.ui.scrollLayout.addRow(layout)

    @QtCore.pyqtSlot(int)
    def valveMoveButtonCurrentIndex_lambda(self, int):
        print "Issued Move from Index: " + str(int)
        currentRotationIndex = self.desiredRotations[int].currentIndex()
        print "Found Rotation Index: " + str(currentRotationIndex)
        
    def closeEvent(self, event):
        pass

    def handleRadioButton(self, boolean):
        which_button = 0
        for i,button in enumerate(self.buttons):
            if button.isChecked():
                which_button = i
        self.valve_pos = which_button

    def handleValveTimer(self):
        print self.valve_pos
        #print self.valve_queue
        #if (len(self.valve_queue) > 0):
        #    last_position = self.valve_queue[-1]
        #    self.valve_queue = []
        #    self.updateValvePosition(last_position)

    def quit(self, boolean):
        self.close()

    def updateValvePosition(self, position):
        if (self.current_position != position):
            self.current_position = position
            print position
            time.sleep(1.0)

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = Window()
    window.show()
    app.exec_()

#
# The MIT License
#
# Copyright (c) 2013 Zhuang Lab, Harvard University
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
