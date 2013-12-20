#!/usr/bin/python

import os
import sys
import time
from PyQt4 import QtCore, QtGui

import ui_simple_fluidics as fluidicsUi
import hamilton
#
# Main window
#
class Window(QtGui.QMainWindow):
    def __init__(self, parent = None):
        QtGui.QMainWindow.__init__(self, parent)
        
        # Define timer for periodic polling of valve status
        self.valve_poll_timer = QtCore.QTimer()        
        self.valve_poll_timer.setInterval(1000)
        self.valve_poll_timer.timeout.connect(self.PollValveStatus)
        
        # ui setup
        self.ui = fluidicsUi.Ui_MainWindow()
        self.ui.setupUi(self)

        # Initialize hamilton class
        self.hamilton = hamilton.HamiltonMVP(verbose = False)
        
        self.currentValvePosition = "Initializing"
        self.ui.currentValveStatus.setText(self.currentValvePosition)

        self.PollValveStatus()
        
        # Connect File Pull Down Signals
        self.ui.actionQuit.triggered.connect(self.Quit)
        self.ui.actionInitializeHamilton.triggered.connect(self.ReinitializeHamilton)

        # Connect Button Pushes
        self.ui.changeValvePosition.released.connect(self.SendValveChangeCommand)

        self.valve_poll_timer.start()

    def closeEvent(self, event):
        self.valve_poll_timer.stop()
        self.hamilton.Close()
    
    def SendValveChangeCommand(self):
        currentValve = self.ui.desiredValvePosition.currentIndex()
        currentDirection = self.ui.desiredRotationDirection.currentIndex()
        self.hamilton.MoveValve(currentValve + 1, direction = currentDirection)
        self.PollValveStatus()
        
    def PollValveStatus(self):
        self.isMoving = not self.hamilton.IsMovementFinished()[0]

        if self.isMoving:
            self.ui.currentValveStatus.setStyleSheet("QLabel { color: red}")
        else:
            self.ui.currentValveStatus.setStyleSheet("QLabel { color: black}")
        
        self.currentValvePosition = self.hamilton.WhereIsValve()[0]
        self.ui.currentValveStatus.setText(self.currentValvePosition)

    def ReinitializeHamilton(self):
        self.hamilton.ResetHamilton()
    
    def Quit(self, boolean):
        self.close()

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
