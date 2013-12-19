#!/usr/bin/python

import os
import sys
import time
from PyQt4 import QtCore, QtGui

import fluidics_ui as fluidicsUi

#
# Main window
#
class Window(QtGui.QMainWindow):
    def __init__(self, parent = None):
        QtGui.QMainWindow.__init__(self, parent)
        self.current_position = 0
        self.valve_timer = QtCore.QTimer()
        self.valve_pos = 0

        self.valve_timer.setInterval(100)
        self.valve_timer.timeout.connect(self.handleValveTimer)

        # ui setup
        self.ui = fluidicsUi.Ui_MainWindow()
        self.ui.setupUi(self)

        self.buttons = [self.ui.pos1RadioButton,
                        self.ui.pos2RadioButton,
                        self.ui.pos3RadioButton,
                        self.ui.pos4RadioButton,
                        self.ui.pos5RadioButton,
                        self.ui.pos6RadioButton,
                        self.ui.pos7RadioButton,
                        self.ui.pos8RadioButton]

        #self.buttons[self.hamilton.getCurrentPosition()].setChecked()

        # connect signals
        self.ui.actionQuit.triggered.connect(self.quit)
        for button in self.buttons:
            button.clicked.connect(self.handleRadioButton)

        self.valve_timer.start()

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
