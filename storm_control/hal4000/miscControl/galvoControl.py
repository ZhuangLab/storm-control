#!/usr/bin/env python
"""
The galvo control UI. Actual control of the hardware is
provided by a waveform functionality from the DAQ.

Jeff Moffitt 11/15
Hazen Babcock 05/17
"""

import fractions
import numpy
from PyQt5 import QtCore, QtGui, QtWidgets

import storm_control.hal4000.halLib.halDialog as halDialog
import storm_control.hal4000.halLib.halMessage as halMessage
import storm_control.hal4000.halLib.halModule as halModule


# UI.
import storm_control.hal4000.qtdesigner.galvo_ui as galvoUi


class GalvoView(halDialog.HalDialog):
    """
    Manages the galvo GUI.
    """
    def __init__(self, configuration = None, **kwds):
        super().__init__(**kwds)
        self.running = False
        self.sampling_rate = configuration.get("sampling_rate")
        self.scan_fn = None

        self.ui = galvoUi.Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.xAmplitudeSpinBox.setValue(configuration.get("x_amp"))
        self.ui.yAmplitudeSpinBox.setValue(configuration.get("y_amp"))
        self.ui.xFrequencySpinBox.setValue(configuration.get("x_freq"))
        self.ui.yFrequencySpinBox.setValue(configuration.get("y_freq"))
        self.ui.xOffsetSpinBox.setValue(configuration.get("x_offset"))
        self.ui.yOffsetSpinBox.setValue(configuration.get("y_offset"))

        self.ui.activateButton.setText("Run")
        self.ui.activateButton.clicked.connect(self.handleActivate)

        self.setEnabled(False)

    def handleActivate(self, boolean):
        if self.running:
            self.ui.activateButton.setText("Run")
            self.toggleControls(True)
            self.stopScan()
        else:
            self.ui.activateButton.setText("Stop")
            self.toggleControls(False)
            self.startScan()
        self.running = not self.running

    def setFunctionality(self, scan_functionality):
        self.scan_fn = scan_functionality
        self.setEnabled(True)

    def startScan(self):
        """
        Start scanning the mirrors in a sinusoidal pattern.
        """
        x_amp = self.ui.xAmplitudeSpinBox.value()
        x_freq = self.ui.xFrequencySpinBox.value()
        x_offset = self.ui.xOffsetSpinBox.value()
        
        y_amp = self.ui.yAmplitudeSpinBox.value()
        y_freq = self.ui.yFrequencySpinBox.value()
        y_offset = self.ui.yOffsetSpinBox.value()

        if not (((x_freq % y_freq) == 0) or ((y_freq % x_freq) == 0)):
            print(">> Warning galvo frequencies are not multiples of each other.")

        freq = max(x_freq, y_freq)
        time = numpy.arange(0.0, 1.0/freq, 1.0/self.sampling_rate)

        # Create waveforms
        wave_x = x_offset + x_amp * numpy.sin(2 * numpy.pi * x_freq * time)
        wave_y = y_offset + y_amp * numpy.sin(2 * numpy.pi * y_freq * time)

        self.scan_fn.waveformOutput(waveforms = [wave_x, wave_y],
                                    sample_rate = self.sampling_rate)
        
    def stopScan(self):
        """
        Stop moving the mirrors & return to zero position.
        """
        self.scan_fn.analogOut([self.ui.xOffsetSpinBox.value(),
                                self.ui.yOffsetSpinBox.value()])

    def toggleControls(self, is_enabled):
        """
        Enable or disable controls to allow the user to 
        change these only when the mirrors are not running.
        """
        self.ui.xAmplitudeSpinBox.setEnabled(is_enabled)
        self.ui.xOffsetSpinBox.setEnabled(is_enabled)
        self.ui.xFrequencySpinBox.setEnabled(is_enabled)
        self.ui.yAmplitudeSpinBox.setEnabled(is_enabled)
        self.ui.yOffsetSpinBox.setEnabled(is_enabled)
        self.ui.yFrequencySpinBox.setEnabled(is_enabled)        


class Galvo(halModule.HalModule):

    def __init__(self, module_params = None, qt_settings = None, **kwds):
        super().__init__(**kwds)
        self.configuration = module_params.get("configuration")

        self.view = GalvoView(module_name = self.module_name,
                              configuration = module_params.get("configuration"))
        self.view.halDialogInit(qt_settings,
                                module_params.get("setup_name") + " galvo control")

    def cleanUp(self, qt_settings):
        self.view.cleanUp(qt_settings)

    def handleResponse(self, message, response):
        if message.isType("get functionality"):
            self.view.setFunctionality(response.getData()["functionality"])

    def processMessage(self, message):

        if message.isType("configure1"):
            self.sendMessage(halMessage.HalMessage(m_type = "add to menu",
                                                   data = {"item name" : "Galvo Control",
                                                           "item data" : "galvo control"}))

            self.sendMessage(halMessage.HalMessage(m_type = "get functionality",
                                                   data = {"name" : self.configuration.get("scan_fn")}))

        elif message.isType("show"):
            if (message.getData()["show"] == "galvo control"):
                self.view.show()

        elif message.isType("start"):
            if message.getData()["show_gui"]:
                self.view.showIfVisible()


#
# The MIT License
#
# Copyright (c) 2017 Zhuang Lab, Harvard University
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
