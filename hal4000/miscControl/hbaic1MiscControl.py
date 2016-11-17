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
import sc_library.parameters as params

# Debugging
import sc_library.hdebug as hdebug

# UIs.
import qtdesigner.hbaic1_misc_ui as miscControlsUi

# Prior filter wheel
import sc_hardware.prior.prior as prior

#
# Misc Control Dialog Box
#
class AMiscControl(miscControl.MiscControl):
    @hdebug.debug
    def __init__(self, hardware, parameters, parent = None):
        miscControl.MiscControl.__init__(self, parameters, parent)

        self.em_filter_pos = 0
        self.em_filter_wheel = prior.Prior(port = hardware.get("port"),
                                           baudrate = hardware.get("baud_rate"))
        
        # Add parameters.
        misc_params = parameters.addSubSection("misc")
        misc_params.add("em_checked", params.ParameterSetBoolean("Change emission filter position during filming",
                                                                 "em_checked",
                                                                 False))
        misc_params.add("em_filter", params.ParameterRangeInt("Emission filter position",
                                                              "em_filter",
                                                              0, 0, 5))
        misc_params.add("em_period", params.ParameterInt("Emission filter update period in frames",
                                                         "em_period",
                                                         60))

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

        # setup (emission) filter wheel
#        self.ui.emFilter6Button.hide()
#        self.ui.emFilter7Button.hide()
#        self.ui.emFilter8Button.hide()
#        self.ui.emFilter9Button.hide()
#        self.ui.emFilter10Button.hide()
        self.em_filters = [[self.ui.emFilter1Button, "Quad"],
                           [self.ui.emFilter2Button, "750"],
                           [self.ui.emFilter3Button, "647"],
                           [self.ui.emFilter4Button, "560"],
                           [self.ui.emFilter5Button, "488"],
                           [self.ui.emFilter6Button, "Empty"]]
        for [afilter, name] in self.em_filters:
            afilter.clicked.connect(self.handleEmFilter)
            afilter.setText(name)
        if self.em_filter_wheel:
            self.em_filters[self.em_filter_wheel.getFilter()-1][0].click()

        self.ui.emCheckBox.setChecked(parameters.get("misc.em_checked"))
        self.ui.emSpinBox.setValue(parameters.get("misc.em_period"))

    @hdebug.debug
    def handleEmFilter(self, bool):
        for i, afilter in enumerate(self.em_filters):
            if afilter[0].isChecked():
                afilter[0].setStyleSheet("QPushButton { color: red}")
                if self.em_filter_wheel:
                    self.em_filter_pos = i
                    self.em_filter_wheel.changeFilter(i+1)
                self.parameters.set("misc.em_filter", i)
            else:
                afilter[0].setStyleSheet("QPushButton { color: black}")

    def newFrame(self, frame, filming):
        if filming:
            if self.ui.emCheckBox.isChecked():
                if (((frame.number + 1) % self.ui.emSpinBox.value()) == 0):
                    self.em_filter_pos += 1
                    self.em_filters[(self.em_filter_pos%5)].click()

    @hdebug.debug
    def newParameters(self, parameters):
        self.parameters.setv("misc.em_checked", self.ui.emCheckBox.isChecked())
        self.parameters.setv("misc.em_period", self.ui.emSpinBox.value())

        self.parameters = parameters

        self.em_filters[self.parameters.get("misc.em_filter")][0].click()
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
