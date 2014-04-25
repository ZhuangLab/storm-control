#!/usr/bin/python
#
## @file
#
# Handle the EPI/TIRF motor for Prism2.
#
# Hazen 11/11
#

import sys
from PyQt4 import QtCore, QtGui

import miscControl

# UIs.
import qtdesigner.prism2_misc_ui as miscControlsUi

# mgmotor (for EPI/TIRF)
import sc_hardware.thorlabs.mgmotorAX as mgmotorAX

#
# Misc Control Dialog Box
#
class AMiscControl(miscControl.MiscControl):
    def __init__(self, parameters, tcp_control, camera_widget, parent = None):
        super(AMiscControl, self).__init__(parameters, tcp_control, camera_widget, parent)

        self.debug = 1

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

        self.ui.EPIButton.clicked.connect(self.goToEPI)
        self.ui.TIRFButton.clicked.connect(self.goToTIRF)
        self.move_timer.timeout.connect(self.updatePosition)

        # set modeless
        self.setModal(False)

        self.epi_position = 18.6
        self.tirf_position = 21.3

        if parameters:
            self.newParameters(parameters)

        # epi/tir stage init
        self.mgmotor = mgmotor.APTUser(self.ui.motorWidget)

    def goToEPI(self, bool):
        if self.debug:
            print " goToEPI"
        self.moveStage(self.epi_position)

    def goToTIRF(self, bool):
        if self.debug:
            print " goToTIRF"
        self.moveStage(self.tirf_position)

    def handleOk(self, bool):
        if self.debug:
            print " handleOk"
        self.hide()

    def moveStage(self, pos):
        self.mgmotor.moveTo(pos)

    def newParameters(self, parameters):
        if self.debug:
            print " newParameters"
        self.debug = parameters.debug
        self.epi_position = parameters.epi_position
        self.tirf_position = parameters.tirf_position

#
# The MIT License
#
# Copyright (c) 2011 Zhuang Lab, Harvard University
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
