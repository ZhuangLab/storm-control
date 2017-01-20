#!/usr/bin/python
#
## @file
#
# The galvo control UI.
#
# Jeff Moffitt 11/15
#

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets


import storm_control.hal4000.qtWidgets.qtAppIcon as qtAppIcon

import storm_control.hal4000.halLib.halModule as halModule

# National instruments control
import storm_control.sc_hardware.nationalInstruments.nicontrol as nicontrol

# Debugging
import storm_control.sc_library.hdebug as hdebug

# UIs.
import storm_control.hal4000.qtdesigner.galvo_ui as galvoUi

## GavloControl
#
# Galvo Control Dialog Box
#
# This is the UI for controlling a set of galvonometer mirrors.
# In its general form, this class could control any sort of XY scan system.
#
class GalvoControl(QtWidgets.QDialog, halModule.HalModule):

    ## __init__
    #
    # @param parameters A parameters object.
    # @param parent The PyQt parent of this object.
    #
    @hdebug.debug
    def __init__(self, hardware, parameters, parent):
        QtWidgets.QMainWindow.__init__(self, parent)
        halModule.HalModule.__init__(self)

        # Define default values
        self.x_offset = 0.0
        self.y_offset = 0.0
        self.x_amp = 1.0
        self.y_amp = 1.0
        self.x_freq = 1000.0 # In Hz
        self.y_freq = 1000.0 # In Hz
        self.running = False
        self.run_during_film = False

        self.home_voltage = [0.0, 0.0]

        self.output_limits = [-10.0, 10.0]
        self.sampleRate = 2500.0 # In Hz
        
        self.ni_task = False

        # Initialize waveform
        self.waveform = False

        # update parameters
        self.parameters = parameters
        
        if parent:
            self.have_parent = True
        else:
            self.have_parent = False

        # UI setup
        self.ui = galvoUi.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(parameters.get("setup_name") + " Galvo Control")
        self.setWindowIcon(qtAppIcon.QAppIcon())

        # Connect signals.
        if self.have_parent:
            self.ui.okButton.setText("Close")
            self.ui.okButton.clicked.connect(self.handleOk)
        else:
            self.ui.okButton.setText("Quit")
            self.ui.okButton.clicked.connect(self.handleQuit)

        self.ui.activateButton.setText("Run")
        self.ui.activateButton.clicked.connect(self.handleActivate)

        # set modeless
        self.setModal(False)

        # Update display
        self.updateDisplay()

        # Initialize to home voltage
        nicontrol.setAnalogLine("USB-6002", 0, self.home_voltage[0])
        nicontrol.setAnalogLine("USB-6002", 1, self.home_voltage[1])

    ## cleanup
    #
    @hdebug.debug
    def cleanup(self):
        pass
        # This will need to eventually close the ni task

    def coerceToRange(self, waveform):
        # UNDER CONSTRUCTION

        return waveform

    ## handleOk
    #
    # Hide the window.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def handleOk(self, bool):
        self.hide()

    ## handleOk
    #
    # Handle press of the activate button.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def handleActivate(self, bool):
        if self.running:
            self.ui.activateButton.setText("Run")
            self.toggleControls(True)
            self.stopTask()
        else:
            self.ui.activateButton.setText("Stop")
            self.updateParameters()
            self.toggleControls(False)
            self.startTask()

    ## updateDisplay
    #
    # Update the display values to reflect the internal values of the class
    #
    # @param bool Dummy parameter.
    #
    def updateDisplay(self):
        self.ui.xOffsetSpinBox.setValue(self.x_offset)
        self.ui.yOffsetSpinBox.setValue(self.y_offset)
        self.ui.xAmplitudeSpinBox.setValue(self.x_amp)
        self.ui.yAmplitudeSpinBox.setValue(self.y_amp)
        self.ui.xFrequencySpinBox.setValue(self.x_freq)
        self.ui.yFrequencySpinBox.setValue(self.y_freq)

    ## toggleControls
    #
    # Enable or disable controls to allow the user to change these only when the mirrors are not running
    #
    # @param bool Dummy parameter.
    #
    def toggleControls(self, isEnabled):
        self.ui.xAmplitudeSpinBox.setEnabled(isEnabled)
        self.ui.xOffsetSpinBox.setEnabled(isEnabled)
        self.ui.xFrequencySpinBox.setEnabled(isEnabled)
        self.ui.yAmplitudeSpinBox.setEnabled(isEnabled)
        self.ui.yOffsetSpinBox.setEnabled(isEnabled)
        self.ui.yFrequencySpinBox.setEnabled(isEnabled)

    ## updateParameters
    #
    # Update the internal values to match the display values
    #
    # @param bool Dummy parameter.
    #
    def updateParameters(self):
        self.x_offset = self.ui.xOffsetSpinBox.value()
        self.y_offset = self.ui.yOffsetSpinBox.value()
        self.x_amp = self.ui.xAmplitudeSpinBox.value()
        self.y_amp = self.ui.yAmplitudeSpinBox.value()
        self.x_freq = self.ui.xFrequencySpinBox.value()
        self.y_freq = self.ui.yFrequencySpinBox.value()    

    ## startTask
    #
    # Build the waveforms and start the mirrors
    #
    # @param bool Dummy parameter.
    #
    def startTask(self):
        # Create NI analog tasks
        self.ni_task = nicontrol.AnalogWaveformOutput("USB-6002", 0)
        self.ni_task.addChannel("USB-6002", 1)

        # Identify the longest period and use as the length of the buffer: NOTE: the higher frequency must be a multiple of the lowest
        duration = max(1/self.x_freq, 1/self.y_freq)
        time = np.arange(0, duration, 1/self.sampleRate)

        # Create waveforms
        wave_x = self.x_offset + self.x_amp * np.sin(2 * np.pi * self.x_freq * time)
        wave_y = self.y_offset + self.y_amp * np.sin(2 * np.pi * self.y_freq * time)
        self.waveform = self.coerceToRange(np.concatenate((wave_x, wave_y)))

        # Send waveform to ni card
        self.ni_task.setWaveform(self.waveform, self.sampleRate, clock = "ctr0out")

        # Start task
        self.ni_task.startTask()

        self.running = True

    ## stopTask
    #
    # Stop the task
    #
    # @param bool Dummy parameter.
    #
    def stopTask(self):
        # Stop current task
        self.ni_task.stopTask()
        self.ni_task.clearTask()

        # Return to home voltage
        nicontrol.setAnalogLine("USB-6002", 0, self.home_voltage[0])
        nicontrol.setAnalogLine("USB-6002", 1, self.home_voltage[1])

        # Update internal state
        self.running = False

    ## handleQuit
    #
    # Close the window.
    #
    # @param bool Dummy parameter.
    #
    @hdebug.debug
    def handleQuit(self, bool):
        if self.running:
            self.stopTask()
        self.close()

    ## closeEvent
    #
    # Close the dialog if it has no parent, otherwise just hide it.
    #
    # @param event A PyQt event.
    #
    @hdebug.debug
    def closeEvent(self, event):
        if self.have_parent:
            event.ignore()
            self.hide()

    ## newParameters
    #
    # Called when a new set of parameters is chosen.
    #
    # @param parameters A parameters object.
    #
    @hdebug.debug
    def newParameters(self, parameters):
        pass

        
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
