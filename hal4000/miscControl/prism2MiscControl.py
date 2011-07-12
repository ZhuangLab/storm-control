#!/usr/bin/python
#
# Handle the EPI/TIRF motor for Prism2.
#
# Hazen 01/10
#

import sys
from PyQt4 import QtCore, QtGui

# UIs.
import qtdesigner.prism2_misc_ui as miscControlsUi

# mgmotor (for EPI/TIRF)
import thorlabs.mgmotorAX as mgmotorAX

#
# Misc Control Dialog Box
#
class AMiscControl(QtGui.QDialog):
    def __init__(self, parameters, tcp_control, parent = None):
        QtGui.QMainWindow.__init__(self, parent)
        self.debug = 1
        if parent:
            self.have_parent = 1
        else:
            self.have_parent = 0

        # UI setup
        self.ui = miscControlsUi.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(parameters.setup_name + " Misc Control")

        # connect signals
        if self.have_parent:
            self.ui.okButton.setText("Close")
            self.connect(self.ui.okButton, QtCore.SIGNAL("clicked()"), self.handleOk)
        else:
            self.ui.okButton.setText("Quit")
            self.connect(self.ui.okButton, QtCore.SIGNAL("clicked()"), self.handleQuit)

        self.connect(self.ui.EPIButton, QtCore.SIGNAL("clicked()"), self.goToEPI)
        self.connect(self.ui.TIRFButton, QtCore.SIGNAL("clicked()"), self.goToTIRF)
        self.connect(self.move_timer, QtCore.SIGNAL("timeout()"), self.updatePosition)

        # set modeless
        self.setModal(False)

        self.epi_position = 18.6
        self.tirf_position = 21.3

        if parameters:
            self.newParameters(parameters)

        # epi/tir stage init
        self.mgmotor = mgmotor.APTUser(self.ui.motorWidget)

    def closeEvent(self, event):
        if self.debug:
            print " closeEvent"
        if self.have_parent:
            event.ignore()
            self.hide()
        else:
            self.quit()

    def goToEPI(self):
        if self.debug:
            print " goToEPI"
        self.moveStage(self.epi_position)

    def goToTIRF(self):
        if self.debug:
            print " goToTIRF"
        self.moveStage(self.tirf_position)

    def handleOk(self):
        if self.debug:
            print " handleOk"
        self.hide()

    def handleQuit(self):
        if self.debug:
            print " handleQuit"
        self.close()

    def moveStage(self, pos):
        self.mgmotor.moveTo(pos)

    def newParameters(self, parameters):
        if self.debug:
            print " newParameters"
        self.debug = parameters.debug
        self.epi_position = parameters.epi_position
        self.tirf_position = parameters.tirf_position

    def quit(self):
        if self.debug:
             print " quit (misc)"
        pass

#
# The MIT License
#
# Copyright (c) 2009 Zhuang Lab, Harvard University
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
