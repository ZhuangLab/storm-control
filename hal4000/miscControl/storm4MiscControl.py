#!/usr/bin/python
#
## @file
#
# Handle filter wheel for STORM4.
#
# Hazen 04/12
#

import time
import sys
from PyQt4 import QtCore, QtGui

import miscControl

# Debugging
import sc_library.hdebug as hdebug

# UIs.
import qtdesigner.storm4_misc_ui as miscControlsUi

# Control
import olympus.ix2ucb as ix2ucb

#
# Misc Control Dialog Box
#
class AMiscControl(miscControl.MiscControl):
    @hdebug.debug
    def __init__(self, hardware, parameters, parent = None):
        miscControl.MiscControl.__init__(self, parameters, parent)

        self.filter_wheel = ix2ucb.IX2UCB(port = "COM3")
        if (not self.filter_wheel.getStatus()):
            self.filter_wheel = False

        # UI setup
        self.ui = miscControlsUi.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(parameters.setup_name + " Misc Control")

        # connect signals
        if self.have_parent:
            self.ui.okButton.setText("Close")
            self.ui.okButton.clicked.connect(self.handleOk)
        else:
            self.ui.okButton.setText("Quit")
            self.ui.okButton.clicked.connect(self.handleQuit)

        # setup filter wheel
        self.filters = [self.ui.filter1Button,
                        self.ui.filter2Button,
                        self.ui.filter3Button,
                        self.ui.filter4Button,
                        self.ui.filter5Button,
                        self.ui.filter6Button]
        for filter in self.filters:
            filter.clicked.connect(self.handleFilter)
        if self.filter_wheel:
            self.filters[self.filter_wheel.getPosition()-1].click()

    @hdebug.debug
    def cleanup(self):
        if self.filter_wheel:
            self.filter_wheel.shutDown()

    @hdebug.debug
    def handleFilter(self, bool):
        for i, filter in enumerate(self.filters):
            if filter.isChecked():
                filter.setStyleSheet("QPushButton { color: red}")
                if self.filter_wheel:
                    self.filter_wheel.setPosition(i+1)
                self.parameters.filter_position = i
            else:
                filter.setStyleSheet("QPushButton { color: black}")

    @hdebug.debug
    def newParameters(self, parameters):
        self.parameters = parameters
        names = parameters.filter_names
        if (len(names) == 6):
            for i in range(6):
                self.filters[i].setText(names[i])
        self.filters[self.parameters.filter_position].click()


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
