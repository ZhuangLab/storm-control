#!/usr/bin/env python
"""
The various ChannelUI classes.

Hazen 04/17
"""

from PyQt5 import QtCore, QtWidgets


class ChannelUI(QtWidgets.QFrame):
    """
    A QWidget for displaying the UI elements associated with
    an illumination channel.
    """
    onOffChange = QtCore.pyqtSignal(object)
    powerChange = QtCore.pyqtSignal(int)

    def __init__(self, name = "", color = None, **kwds):
        super().__init__(**kwds)

        self.color = color
        self.enabled = True

        self.setLineWidth(2)
        self.setStyleSheet("background-color: rgb(" + self.color + ");")
        self.setFrameShape(QtWidgets.QFrame.Panel)
        self.setFrameShadow(QtWidgets.QFrame.Raised)
        self.setLayout(QtWidgets.QVBoxLayout())
        self.setFixedWidth(50)
        self.layout().setContentsMargins(0,0,0,0)
        self.layout().setSpacing(1)

        # Text label.
        self.wavelength_label = QtWidgets.QLabel(self)
        self.wavelength_label.setText(name)
        self.wavelength_label.setAlignment(QtCore.Qt.AlignCenter)
        self.layout().addWidget(self.wavelength_label)

        # Container for the power slider (if any).
        self.container_widget = QtWidgets.QWidget(self)
        self.container_widget.setFixedHeight(140)
        self.container_widget.setStyleSheet("background-color: white;")
        self.layout().addWidget(self.container_widget)
        
        self.container_layout = QtWidgets.QVBoxLayout(self.container_widget)
        self.container_layout.setContentsMargins(0,0,0,0)
        self.container_layout.setSpacing(1)

        # Power on/off radio button.
        self.on_off_button = QtWidgets.QRadioButton(self)
        self.layout().addWidget(self.on_off_button)
        self.layout().setAlignment(self.on_off_button, QtCore.Qt.AlignCenter)
        
        # Connect signals
        self.on_off_button.clicked.connect(self.handleOnOffChange)

    def disableChannel(self):
        """
        Disables all the UI elements of the channel.
        """
        self.setOnOff(False)
        self.setStyleSheet("background-color: rgb(128,128,128);")
        self.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.wavelength_label.setStyleSheet("QLabel { color: rgb(200,200,200)}")
        self.on_off_button.setCheckable(False)
        self.enabled = False

    def enableChannel(self, was_on = False):
        """
        Enables all the UI elements of the channel.
        """
        self.setStyleSheet("background-color: rgb(" + self.color + ");")
        self.setFrameShadow(QtWidgets.QFrame.Raised)
        self.wavelength_label.setStyleSheet("QLabel { color: black}")
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

    def __init__(self, minimum = 0, maximum = 1, **kwds):
        super().__init__(**kwds)

        self.buttons = []
        #self.cur_y = 202
        self.max_amplitude = maximum
        self.min_amplitude = minimum

        # Current power label.
        self.power_label = QtWidgets.QLabel(self.container_widget)
        self.power_label.setText("")
        self.power_label.setAlignment(QtCore.Qt.AlignCenter)
        self.container_layout.addWidget(self.power_label)

        # Slider for controlling the power.
        self.powerslider = QtWidgets.QSlider(self.container_widget)
        self.powerslider.setMinimum(minimum)
        self.powerslider.setMaximum(maximum)
        self.powerslider.setOrientation(QtCore.Qt.Vertical)
        page_step = 0.1 * (maximum - minimum)
        if (page_step > 1.0):
            self.powerslider.setPageStep(page_step)
        self.powerslider.setSingleStep(1)
        self.container_layout.addWidget(self.powerslider)
        self.container_layout.setAlignment(self.powerslider,
                                           QtCore.Qt.AlignCenter)
        self.powerslider.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                                             QtWidgets.QSizePolicy.Expanding))

        self.powerslider.valueChanged.connect(self.handleAmplitudeChange)

    def disableChannel(self):
        super().disableChannel()
        self.power_label.setStyleSheet("QLabel { color: rgb(200,200,200)}")
        self.powerslider.setEnabled(False)
        for button in self.buttons:
            button.setEnabled(False)

    def enableChannel(self, was_on = False):
        super().enableChannel(was_on)
        self.power_label.setStyleSheet("QLabel { color: black}")
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
        #self.setGeometry(6, y_loc, 38, 20)
        #self.setAligment(QtCore.Qt.AlignCenter)
        self.setStyleSheet("background-color: None;")

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
