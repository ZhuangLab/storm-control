#!/usr/bin/python
#
## @file
#
# Handle lamp/laser and filter wheel for STORM2.
#
# Hazen 11/11
#

import time
import sys
from PyQt4 import QtCore, QtGui

import miscControl

# Debugging
import sc_library.hdebug as hdebug

# UIs.
import qtdesigner.storm2_misc_ui as miscControlsUi

# Emission filter wheel
import sc_hardware.thorlabs.FW102C as FW102C

# Prior filter wheel
import stagecontrol.storm2StageControl as filterWheel

#
# Misc Control Dialog Box
#
class AMiscControl(miscControl.MiscControl):
    @hdebug.debug
    def __init__(self, hardware, parameters, parent = None):
        miscControl.MiscControl.__init__(self, parameters, parent)

        self.em_filter_pos = 0
        self.em_filter_wheel = filterWheel.QPriorFilterWheel()
        #if not self.em_filter_wheel.live:
        #    self.em_filter_wheel = False
        self.filter_wheel = filterWheel.QPriorFilterWheel()

        # UI setup
        self.ui = miscControlsUi.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(parameters.get("setup_name") + " Misc Control")

        # connect signals
        if self.have_parent:
            self.ui.okButton.setText("Close")
            self.ui.okButton.clicked.connect(self.handleOk)
        else:
            self.ui.okButton.setText("Quit")
            self.ui.okButton.clicked.connect(self.handleQuit)

        # setup (turret) filter wheel
        self.filters = [self.ui.filter1Button,
                        self.ui.filter2Button,
                        self.ui.filter3Button,
                        self.ui.filter4Button,
                        self.ui.filter5Button,
                        self.ui.filter6Button]
        for afilter in self.filters:
            afilter.clicked.connect(self.handleFilter)
        if self.filter_wheel:
            self.filters[self.filter_wheel.getPosition(1)-1].click()

        # setup (emission) filter wheel
        self.ui.emFilter5Button.hide()
        self.ui.emFilter6Button.hide()
        self.ui.emFilter7Button.hide()
        self.ui.emFilter8Button.hide()
        self.ui.emFilter9Button.hide()
        self.ui.emFilter10Button.hide()
        self.em_filters = [self.ui.emFilter1Button,
                           self.ui.emFilter2Button,
                           self.ui.emFilter3Button,
                           self.ui.emFilter4Button,
                           self.ui.emFilter5Button,
                           self.ui.emFilter6Button,
                           self.ui.emFilter7Button,
                           self.ui.emFilter8Button,
                           self.ui.emFilter9Button,
                           self.ui.emFilter10Button]
        for afilter in self.em_filters:
            afilter.clicked.connect(self.handleEmFilter)
        if self.em_filter_wheel:
            self.em_filters[self.filter_wheel.getPosition(2)-1].click()

        self.ui.emCheckBox.setChecked(parameters.get("misc.em_checked"))
        self.ui.emSpinBox.setValue(parameters.get("misc.em_period"))

    @hdebug.debug
    def handleEmFilter(self, bool):
        for i, afilter in enumerate(self.em_filters):
            if afilter.isChecked():
                afilter.setStyleSheet("QPushButton { color: red}")
                if self.em_filter_wheel:
                    self.em_filter_pos = i
                    self.em_filter_wheel.setPosition(i+1, 2)
                self.parameters.set("misc.em_filter", i)
            else:
                afilter.setStyleSheet("QPushButton { color: black}")

    @hdebug.debug
    def handleFilter(self, bool):
        for i, filter in enumerate(self.filters):
            if filter.isChecked():
                filter.setStyleSheet("QPushButton { color: red}")
                if self.filter_wheel:
                    self.em_filter_pos = i
                    self.filter_wheel.setPosition(i+1, 1)
                self.parameters.set("misc.filter_position", i)
            else:
                filter.setStyleSheet("QPushButton { color: black}")

    def newFrame(self, frame, filming):
        if filming:
            if self.ui.emCheckBox.isChecked():
                if (((frame.number + 1) % self.ui.emSpinBox.value()) == 0):
                    self.em_filter_pos += 1
                    self.em_filters[(self.em_filter_pos%4)].click()

    @hdebug.debug
    def newParameters(self, parameters):
        self.parameters.em_checked = self.ui.emCheckBox.isChecked()
        self.parameters.em_period = self.ui.emSpinBox.value()

        self.parameters = parameters
        names = parameters.get("misc.filter_names")
        if (len(names) == 6):
            for i in range(6):
                self.filters[i].setText(names[i])

        self.filters[self.parameters.get("misc.filter_position")].click()
        self.em_filters[self.parameters.get("misc.em_filter")].click()
        self.ui.emCheckBox.setChecked(self.parameters.get("misc.em_checked"))
        self.ui.emSpinBox.setValue(self.parameters.get("misc.em_period"))

    def startFilm(self, film_name, run_shutters):
        if self.ui.emCheckBox.isChecked():        
            self.em_filters[0].click()

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
