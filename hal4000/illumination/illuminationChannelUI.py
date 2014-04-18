#!/usr/bin/python
#
## @file
#
# This file contains the various ChannelUI classes.
#
# Hazen 04/14
#

from PyQt4 import QtCore, QtGui

## ChannelUI
#
# A QWidget for displaying the UI elements associated with
# an illumination channel.
#
class ChannelUI(QtGui.QFrame):
    onOffChange = QtCore.pyqtSignal(object)
    powerChange = QtCore.pyqtSignal(int)

    ## __init__
    #
    # @param name The name of the channel (a text string).
    # @param color The background color to use for the channel [red, green, blue].
    # @param parameters The parameters to use in the initial channel setup.
    # @param parent The PyQt parent of this object.
    #
    def __init__(self, number, name, color, parameters, parent):
        QtGui.QFrame.__init__(self, parent):

        self.parameters = parameters

        self.setStyleSheet("background-color: rgb(" + color + ");")
        self.setFrameShape(QtGui.QFrame.StyledPanel)
        self.setFrameShadow(QtGui.QFrame.Raised)
        self.resize(50, 204)

        # Text label.
        self.wavelength_label = QtGui.QLabel(self)
        self.wavelength_label.setGeometry(5, 5, 40, 10)
        self.wavelength_label.setText(name)
        self.wavelength_label.setAlignment(QtCore.Qt.AlignCenter)

        # Power on/off radio button.
        self.on_off_button = QtGui.QRadioButton(self)
        self.on_off_button.setGeometry(18, self.height() - 24, 18, 18)

        # Connect signals
        self.on_off_button.clicked.connect(self.handleOnOffChange)

    ## getAmplitude
    #
    # @return The current amplitude.        
    #
    def getAmplitude(self):
        if (self.on_off_button.isChecked()):
            return 0
        else:
            return 1

    ## handleOnOffChange
    #
    # Called when the on/off radio button is pressed.
    #
    # @param on_off The state of the radio button.
    #
    def handleOnOffChange(self, on_off):
        self.onOffChange.emit(on_off)

    ## newParameters
    #
    # @param parameters A parameters XML object.
    # @param channel_number The channel number.
    #
    def newParameters(self, parameters, channel_number):
        if self.parameters:
            self.parameters.default_power[channel_number] = self.getAmplitude()
            self.parameters.on_off_state[channel_number] = self.on_off_state.isChecked()

        self.parameters = parameters
        self.on_off_button.setChecked(self.parameters.on_off_state[channel_number])

    ## updatePowerText
    #
    # @param new_text The new text string to display.
    #
    def updatePowerText(self, new_text):
        pass

#
# The MIT License
#
# Copyright (c) 2014 Zhuang Lab, Harvard University
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
