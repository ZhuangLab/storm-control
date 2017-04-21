#!/usr/bin/env python
"""
The various ChannelUI classes.

Hazen 04/17
"""

import os

from PyQt5 import QtCore, QtWidgets


def loadStyleSheet(name):
    text = ""
    with open(os.path.join(os.path.dirname(__file__), name)) as fp:
        text += fp.read()
    return text

    
class ChannelUI(QtWidgets.QFrame):
    """
    A QWidget for displaying the UI elements associated with
    an illumination channel.
    """
    onOffChange = QtCore.pyqtSignal(object)
    powerChange = QtCore.pyqtSignal(int)

    def __init__(self, name = "", color = None, **kwds):
        super().__init__(**kwds)

        self.enabled = True

        # FIXME: These styles could be better..
        self.disabled_style = loadStyleSheet("disabled_style.qss")
        self.enabled_style = "QFrame { background-color: rgb(" + color + ");}\n"
        self.enabled_style += loadStyleSheet("enabled_style.qss")

        self.setFixedWidth(50)
        self.setLineWidth(2)
        self.setStyleSheet(self.enabled_style)
   
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_layout.setSpacing(1)

        # Text label.
        self.wavelength_label = QtWidgets.QLabel(self)
        self.wavelength_label.setText(name)
        self.wavelength_label.setAlignment(QtCore.Qt.AlignCenter)
        
        self.main_layout.addWidget(self.wavelength_label)

        # Container for the power slider (if any).
        self.slider_widget = QtWidgets.QWidget(self)

        #
        # FIXME: This is a mistake if none of the channels have a power
        #        slider.
        #
        self.slider_widget.setMinimumHeight(150)

        self.slider_layout = QtWidgets.QVBoxLayout(self.slider_widget)
        self.slider_layout.setContentsMargins(0,0,0,0)
        self.slider_layout.setSpacing(1)

        self.main_layout.addWidget(self.slider_widget)

        # Power on/off radio button.
        self.on_off_button = QtWidgets.QRadioButton(self)
        
        self.main_layout.addWidget(self.on_off_button)
        self.main_layout.setAlignment(self.on_off_button, QtCore.Qt.AlignCenter)

        # Spacer at the bottom.
        self.spacer_item = QtWidgets.QSpacerItem(1, 1,
                                                 QtWidgets.QSizePolicy.Minimum,
                                                 QtWidgets.QSizePolicy.Expanding)
        self.main_layout.addItem(self.spacer_item)

        # Connect signals
        self.on_off_button.clicked.connect(self.handleOnOffChange)

    def disableChannel(self):
        """
        Disables all the UI elements of the channel.
        """
        self.setOnOff(False)
        self.setStyleSheet(self.disabled_style)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.on_off_button.setCheckable(False)
        self.enabled = False

    def enableChannel(self, was_on = False):
        """
        Enables all the UI elements of the channel.
        """
        self.setStyleSheet(self.enabled_style)
        self.setFrameShadow(QtWidgets.QFrame.Raised)
        self.on_off_button.setCheckable(True)
        self.setOnOff(was_on)
        self.enabled = True

    def getAmplitude(self):
        if self.on_off_button.isChecked():
            return 1.0
        else:
            return 0.0

    def handleOnOffChange(self, on_off):
        """
        Called when the on/off radio button is pressed.
        """
        self.onOffChange.emit(on_off)

    def isEnabled(self):
        return self.enabled

    def isOn(self):
        return self.on_off_button.isChecked()

    def newSettings(self, on, power):
        self.setOnOff(on)

    def remoteIncPower(self, power_inc):
        pass

    def remoteSetPower(self, new_power):
        if self.enabled:
            if (new_power > 0.5):
                self.setOnOff(True)
            else:
                self.setOnOff(False)

    def setOnOff(self, state):
        if (state != self.on_off_button.isChecked()):
            self.on_off_button.setChecked(state)
            self.handleOnOffChange(state)

    def setupButtons(self, button_data):
        pass

    def startFilm(self):
        self.on_off_button.setEnabled(False)

    def stopFilm(self):
        self.on_off_button.setEnabled(True)


class ChannelUIAdjustable(ChannelUI):
    """
    A QWidget for displaying the UI elements associated with
    an adjustable illumination channel.
    """

    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.buttons = []
        self.max_amplitude = 1
        self.min_amplitude = 0

        # Current power label.
        self.power_label = QtWidgets.QLabel(self.slider_widget)
        self.power_label.setAlignment(QtCore.Qt.AlignCenter)
        
        self.slider_layout.addWidget(self.power_label)

        # Slider for controlling the power.
        self.powerslider = QtWidgets.QSlider(self.slider_widget)
        self.powerslider.setOrientation(QtCore.Qt.Vertical)
        self.powerslider.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                       QtWidgets.QSizePolicy.Expanding)

        self.slider_layout.addWidget(self.powerslider)

        # FIXME: If I knew what I was doing I should be able to do this
        #        using the stylesheet?
        self.powerslider.setFixedWidth(25)
        self.slider_layout.setAlignment(self.powerslider, QtCore.Qt.AlignHCenter)
                
    def configureSlider(self, minimum, maximum):
        """
        This is called once we have obtained amplitude functionality 
        that backs the slider. The functionality sets the range
        for the slider.
        """
        self.max_amplitude = maximum
        self.min_amplitude = minimum

        self.powerslider.setMaximum(maximum)
        self.powerslider.setMinimum(minimum)

        page_step = 0.1 * (maximum - minimum)
        if (page_step > 1.0):
            self.powerslider.setPageStep(page_step)
        self.powerslider.setSingleStep(1)

        #
        # Why 2? We need the initial value to be a number that is not
        # the default power, otherwise the slider text won't get updated
        # at start-up.
        #
        self.setAmplitude(2)
        
        self.powerslider.valueChanged.connect(self.handleAmplitudeChange)
        
    def disableChannel(self):
        super().disableChannel()
        self.powerslider.setEnabled(False)
        for button in self.buttons:
            button.setEnabled(False)

    def enableChannel(self, was_on = False):
        super().enableChannel(was_on)
        self.powerslider.setEnabled(True)
        for button in self.buttons:
            button.setEnabled(True)

    def getAmplitude(self):
        return self.powerslider.value()

    def handleAmplitudeChange(self, amplitude):
        self.powerChange.emit(amplitude)

    def newSettings(self, on, power):
        self.setOnOff(on)
        self.setAmplitude(power)

    def remoteIncPower(self, power_inc):
        if self.enabled:
            self.setAmplitude(self.powerslider.value() + power_inc)

    def remoteSetPower(self, new_power):
        if self.enabled:
            self.setAmplitude(new_power)

    def setAmplitude(self, amplitude):
        if (amplitude != self.powerslider.value()):
            self.powerslider.setValue(amplitude)

    def setupButtons(self, button_data):

        # Remove spacer at the end.
        self.main_layout.removeItem(self.spacer_item)
        
        # Make sure we have enough buttons.
        while (len(self.buttons) < len(button_data)):
            new_button = PowerButton(parent = self)
            new_button.powerChange.connect(self.setAmplitude)
            self.layout().addWidget(new_button)
            self.buttons.append(new_button)
            #self.cur_y += 22

        # Hide all the buttons.
        for button in self.buttons:
            button.hide()

        # Set text and value of the buttons we'll use & show them.
        amp_range = float(self.max_amplitude - self.min_amplitude)
        for i in range(len(button_data)):
            self.buttons[i].setText(button_data[i][0])
            self.buttons[i].setValue(int(round(button_data[i][1] * amp_range + self.min_amplitude)))
            self.buttons[i].show()

        # Add spacer again.
        self.main_layout.addItem(self.spacer_item)
        
        # Resize based on number of visible buttons.
        #self.setFixedSize(48, 248 + 22 * len(button_data))

    def updatePowerText(self, new_text):
        self.power_label.setText(new_text)


class PowerButton(QtWidgets.QPushButton):
    """
    A push button specialized for amplitude / power control.
    """
    powerChange = QtCore.pyqtSignal(int)

    def __init__(self, **kwds):
        super().__init__(**kwds)
        self.value = 0.0

        self.clicked.connect(self.handleClicked)

    def handleClicked(self, boolean):
        self.powerChange.emit(self.value)

    def setValue(self, value):
        self.value = value

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
