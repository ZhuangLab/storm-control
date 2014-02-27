#!/usr/bin/python
#
## @file
#
# Widgets for illumination control and display.
#
# Hazen 03/12
#

from PyQt4 import QtCore, QtGui
from xml.dom import Node

## XMLToChannelObject
#
# Channel settings object, created based on the XML descriptor file.
#
class XMLToChannelObject():

    ## __init__
    #
    # Creates the object attributes based on the XML.
    #
    # @param block_node The XML node that corresponds to the settings for the channel.
    #
    def __init__(self, block_node):
        for node in block_node:
            if node.nodeType == Node.ELEMENT_NODE:
                slot = node.nodeName
                value = node.firstChild.nodeValue
                type = node.attributes.item(0).value
                if type == "int":
                    setattr(self, slot, int(value))
                elif type == "float":
                    setattr(self, slot, float(value))
                elif type == "boolean":
                    if value.upper() == "TRUE":
                        setattr(self, slot, 1)
                    else:
                        setattr(self, slot, 0)
                else:
                    setattr(self, slot, value)
        if hasattr(self, "max_voltage"):
            self.range = self.max_voltage - self.min_voltage
        else:
            self.range = 1.0
            self.min_voltage = 0.0
        if not hasattr(self, "amplitude"):
            self.amplitude = 1.0


## QChannel
#
# Master widget for illumination channel display and control. 
#
# New widgets are created each time the parameters are changed.
#
class QChannel(QtGui.QWidget):

    ## __init__
    #
    # @param parent The PyQt parent of this widget.
    # @param settings The settings object associated with the channel.
    # @param default_power The initial amplitude of the channel.
    # @param x_pos The x position in the parent widget.
    # @param width The width of the widget.
    # @param height The height of the widget.
    #
    def __init__(self, parent, settings, default_power, x_pos, width, height):
        QtGui.QWidget.__init__(self, parent)

        self.cmd_queue = None
        self.channel_settings = settings
        self.current_amplitude = int(float(settings.amplitude) * default_power)
        self.displayed_amplitude = default_power
        self.inFskMode = 0
        self.filming_on = 0
        self.shutter_queue = None

        self.setGeometry(x_pos, 0, width, height)

        # container frame
        self.channel_frame = QtGui.QFrame(self)
        self.channel_frame.setGeometry(0, 0, width, height)
        self.channel_frame.setStyleSheet("background-color: rgb(" + settings.color + ");")
        self.channel_frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.channel_frame.setFrameShadow(QtGui.QFrame.Raised)

        # text label
        self.channel_frame.wavelength_label = QtGui.QLabel(self.channel_frame)
        self.channel_frame.wavelength_label.setGeometry(5, 5, 40, 10)
        self.channel_frame.wavelength_label.setText(settings.description)
        self.channel_frame.wavelength_label.setAlignment(QtCore.Qt.AlignCenter)

    ## amOn
    #
    # @return True/False if the channel associates with this widget is currently on.
    #
    def amOn(self):
        return (self.channel_frame.on_off_button.isChecked() or self.filming_on)

    ## amplitudeChange
    #
    # @param amplitude The new channel amplitude.
    #
    def amplitudeChange(self, amplitude):
        pass

    ## getCurrentAmplitude
    #
    # @return The amplitude of the channel in internal units.
    #
    def getCurrentAmplitude(self):
        return self.current_amplitude

    ## getCurrentDefaultPower
    #
    # @return The amplitude of the channel in displayed units (0.0 - 1.0).
    #
    def getCurrentDefaultPower(self):
        return float(self.current_amplitude)/float(self.channel_settings.amplitude)

    ## getDisplayedAmplitude
    #
    # FIXME: Is this different from getCurrentDefaultPower?
    #
    # @return The amplitude of the channel that is displayed.
    #
    def getDisplayedAmplitude(self):
        return self.displayed_amplitude

    ## fskOnOff
    #
    # Turn on/off frequency shift key mode (for an AOTF).
    #
    # @param on True/False.
    #
    def fskOnOff(self, on):
        pass

    ## incDisplayedAmplitude
    #
    # Increment the displayed amplitude.
    #
    # @param power_inc The amount to increment by.
    #
    def incDisplayedAmplitude(self, power_inc):
        pass

    ## onOffChange
    #
    # Update the UI when the channel is turned on or off.
    #
    # @param bool Dummy parameter.
    #
    def onOffChange(self, bool):
        self.uiUpdate()

    ## setCmdQueue
    #
    # This sets the object (command queue) that the channel will use to talk
    # to the hardware that is physically associated with the channel.
    #
    # @param queue A command queue object.
    #
    def setCmdQueue(self, queue):
        self.cmd_queue = queue

    ## setDisplayedAmplitude
    #
    # Set the displayed amplitude.
    #
    # @param power The desired amplitude (0.0 - 1.0)
    #
    def setDisplayedAmplitude(self, power):
        pass

    ## setFilmMode
    #
    # All the channels that are used in a shutters file are turned on at
    # the start of filming. All the channels that are not used are turned off
    # and cannot be used during filming. This only applies when the run
    # shutters check box is checked.
    #
    # @param on True/False
    #
    def setFilmMode(self, on):
        if on:
            self.filming_on = 1
        else:
            self.filming_on = 0

    ## setFrequency
    #
    # Set the frequencies of a channel of an AOTF.
    #
    def setFrequency(self):
        pass

    ## setShutterQueue
    #
    # This sets the shutter object (shutter queue) that the channel will use
    # to talk to a mechanical shutter that may be associated with the channel.
    #
    # @param queue A shutter queue object.
    #
    def setShutterQueue(self, queue):
        self.shutter_queue = queue

    ## shutter
    #
    # Open or close the shutter associated with the channel of on is True and
    # the diplayed amplitude of the channel is greater than zero. Does nothing
    # if there is no shutter.
    #
    # @param on True/False
    #
    def shutter(self, on):
        if self.shutter_queue:
            if on and (self.displayed_amplitude > 0.0):
                self.shutter_queue.setShutter(True,
                                              self.channel_settings.ni_board,
                                              self.channel_settings.dig_line)
            else:
                self.shutter_queue.setShutter(False,
                                              self.channel_settings.ni_board,
                                              self.channel_settings.dig_line)

    ## uiUpdate
    #
    # Update the hardware when the UI changes, for example the slider changes.
    #
    def uiUpdate(self):
        pass

    ## update
    #
    # Update the hardware.
    #
    # @param on True/False the channel is on/off.
    #
    def update(self, on):
        pass


## QAdjustableChannel
#
# QChannel specialized for those channels with electronically adjustable illumination control.
# The idea is that there is an internal power that goes to the AOTF, laser, etc. and then
# there is the displayed power which ranges from 0.0 - 1.0. All power change requests to
# the channel are in the range 0.0 - 1.0 and the channel handles converting these value into
# a meaningful value for the hardware. There is some fiddling because the slider only supports
# integer values.
#
class QAdjustableChannel(QChannel):

    ## __init__
    #
    # @param parent The PyQt parent of this widget.
    # @param settings The settings object associated with the channel.
    # @param default_power The initial amplitude of the channel.
    # @param on_off_state Is the channel on or off.
    # @param buttons An array of buttons for the channel (such as "Low" and "Max").
    # @param x_pos The x position in the parent widget.
    # @param width The width of the widget.
    # @param height The height of the widget.
    #
    def __init__(self, parent, settings, default_power, on_off_state, buttons, x_pos, width, height):
        QChannel.__init__(self, parent, settings, default_power, x_pos, width, height)

        # current power label
        self.channel_frame.power_label = QtGui.QLabel(self.channel_frame)
        self.channel_frame.power_label.setGeometry(5, 19, 40, 10)
        self.channel_frame.power_label.setText("{0:.4f}".format(default_power))
        self.channel_frame.power_label.setAlignment(QtCore.Qt.AlignCenter)

        # power slider
        self.channel_frame.powerslider = QtGui.QSlider(self.channel_frame)
        self.channel_frame.powerslider.setGeometry(13, 34, 24, 141)
        self.channel_frame.powerslider.setMinimum(0)
        self.channel_frame.powerslider.setMaximum(settings.amplitude)
        self.channel_frame.powerslider.setValue(int(float(settings.amplitude) * default_power))
        self.channel_frame.powerslider.setPageStep(0.1 * settings.amplitude)
        self.channel_frame.powerslider.setSingleStep(1)
        
        # power buttons
        y = 180
        self.channel_frame.buttons = []
        self.channel_frame.buttons_fns = []

        # This generates the function that is connected to the button that
        # will set the power appropriately when the button is pressed. It
        # did not work to just use lambda in the for loop, presumably because
        # the button variable is not properly closed over.
        def button_fn(power):
            return lambda: self.channel_frame.powerslider.setValue(int(float(self.channel_settings.amplitude) * power))
        for button in buttons:
            # create the button
            temp = QtGui.QPushButton(self.channel_frame)
            temp.setStyleSheet("background-color: None;")
            temp.setGeometry(6, y, 38, 20)
            temp.setText(str(button[0]))
            self.channel_frame.buttons.append(temp)
            # connect it
            temp_fn = button_fn(button[1])
            self.channel_frame.buttons_fns.append(temp_fn)
            QtCore.QObject.connect(temp, QtCore.SIGNAL("clicked()"), temp_fn)
        
            y += 22

        # power on/off radio button
        self.channel_frame.on_off_button = QtGui.QRadioButton(self.channel_frame)
        self.channel_frame.on_off_button.setGeometry(18, height - 24, 18, 18)
        if on_off_state:
            self.channel_frame.on_off_button.setChecked(True)
        else:
            self.channel_frame.on_off_button.setChecked(False)

        # connect signals
        self.channel_frame.powerslider.valueChanged.connect(self.amplitudeChange)
        self.channel_frame.on_off_button.clicked.connect(self.onOffChange)

        self.show()

    ## amplitudeChange
    #
    # Handles when the power slider is changed.
    #
    # @param amplitude The new value of the power slider
    #
    def amplitudeChange(self, amplitude):
        self.current_amplitude = amplitude
        self.displayed_amplitude = float(amplitude)/float(self.channel_settings.amplitude)
        self.channel_frame.power_label.setText("{0:.4f}".format(self.displayed_amplitude))
        self.uiUpdate()

    ## incDisplayedAmplitude
    #
    # @param power_inc The amount to increment by.
    #
    def incDisplayedAmplitude(self, power_inc):
        new_power = self.displayed_amplitude + power_inc
        self.setDisplayedAmplitude(new_power)

    ## setDisplayedAmplitude
    #
    # @param power The new amplitude (0.0 - 1.0).
    #
    def setDisplayedAmplitude(self, power):
        self.channel_frame.powerslider.setValue(int(round((float(self.channel_settings.amplitude) * power), 0)))

## QAOTFChannel
#
# QChannel specialized for AOTF control.
#
class QAOTFChannel(QAdjustableChannel):

    ## __init__
    #
    # @param parent The PyQt parent of this widget.
    # @param settings The settings object associated with the channel.
    # @param default_power The initial amplitude of the channel.
    # @param on_off_state Is the channel on or off.
    # @param buttons An array of buttons for the channel (such as "Low" and "Max").
    # @param x_pos The x position in the parent widget.
    # @param width The width of the widget.
    # @param height The height of the widget.
    #
    def __init__(self, parent, settings, default_power, on_off_state, buttons, x_pos, width, height):
        self.freq_set = False
        QAdjustableChannel.__init__(self, parent, settings, default_power, on_off_state, buttons, x_pos, width, height)

    ## fskOnOff
    #
    # This turns FSK mode on or off on the channel and sets the frequencies accordingly.
    #
    # @param on True/False.
    #
    def fskOnOff(self, on):
        off_freq = 20.0
        if on:
            if not(self.inFskMode):
                self.inFskMode = 1
                self.cmd_queue.fskOnOff(self.channel_settings.aotf_channel, on)
                self.cmd_queue.setFrequencies(self.channel_settings.aotf_channel,
                                              [off_freq, self.channel_settings.frequency, off_freq, off_freq])
        else:
            if self.inFskMode:
                self.inFskMode = 0
                self.cmd_queue.fskOnOff(self.channel_settings.aotf_channel, on)
                self.cmd_queue.setFrequency(self.channel_settings.aotf_channel,
                                            self.channel_settings.frequency)

    ## setFrequency
    #
    # Set the frequency of the AOTF for this channel.
    #
    def setFrequency(self):
        self.cmd_queue.setFrequency(self.channel_settings.aotf_channel,
                                    self.channel_settings.frequency)

    ## uiUpdate
    #
    # Put a request in the AOTF queue to update the channel based on a change in UI (power slider or on/off button).
    #
    def uiUpdate(self):
        self.cmd_queue.addRequest(self.amOn(),
                                  self.channel_settings.aotf_channel,
                                  self.current_amplitude)

    ## update
    #
    # Tell the AOTF queue to update the channel "immediately".
    #
    # @param on True/False.
    #
    def update(self, on):
        self.cmd_queue.setAmplitude(on, self.channel_settings.aotf_channel, self.current_amplitude)


## QAOTFChannelWShutter
#
# QChannel specialized for AOTF control & electronic shutter.
#
class QAOTFChannelWShutter(QAOTFChannel):

    ## __init__
    #
    # @param parent The PyQt parent of this widget.
    # @param settings The settings object associated with the channel.
    # @param default_power The initial amplitude of the channel.
    # @param on_off_state Is the channel on or off.
    # @param buttons An array of buttons for the channel (such as "Low" and "Max").
    # @param x_pos The x position in the parent widget.
    # @param width The width of the widget.
    # @param height The height of the widget.
    #
    def __init__(self, parent, settings, default_power, on_off_state, buttons, x_pos, width, height):
        QAOTFChannel.__init__(self, parent, settings, default_power, on_off_state, buttons, x_pos, width, height)

    ## uiUpdate
    #
    # Open the shutter (if necessary) and call parent uiUpdate method.
    #
    def uiUpdate(self):
        self.shutter(self.amOn())
        QAOTFChannel.uiUpdate(self)

    ## update
    #
    # Open the shutter (if necessary) and call parent update method.
    #
    # @param on True/False
    #
    def update(self, on):
        self.shutter(on)
        QAOTFChannel.update(self, on)

## QCubeChannel
#
# QChannel specialized for Coherent cube (or obis) control.
#
class QCubeChannel(QAdjustableChannel):

    ## __init__
    #
    # @param parent The PyQt parent of this widget.
    # @param settings The settings object associated with the channel.
    # @param default_power The initial amplitude of the channel.
    # @param on_off_state Is the channel on or off.
    # @param buttons An array of buttons for the channel (such as "Low" and "Max").
    # @param x_pos The x position in the parent widget.
    # @param width The width of the widget.
    # @param height The height of the widget.
    #
    def __init__(self, parent, settings, default_power, on_off_state, buttons, x_pos, width, height):
        QAdjustableChannel.__init__(self, parent, settings, default_power, on_off_state, buttons, x_pos, width, height)

    ## uiUpdate
    #
    # Put a request in the command queue to update the channel based on a change in UI (power slider or on/off button).
    #
    def uiUpdate(self):
        self.cmd_queue.addRequest(self.amOn(), self.current_amplitude * 0.01)

    ## update
    #
    # Tell the command queue to update the channel "immediately".
    #
    # @param on True/False.
    #
    def update(self, on):
        self.cmd_queue.setAmplitude(on, self.current_amplitude * 0.01)

#
# QChannel specialized for Coherent cube control & electronic shutter.
#
class QCubeChannelWShutter(QCubeChannel):

    ## __init__
    #
    # @param parent The PyQt parent of this widget.
    # @param settings The settings object associated with the channel.
    # @param default_power The initial amplitude of the channel.
    # @param on_off_state Is the channel on or off.
    # @param buttons An array of buttons for the channel (such as "Low" and "Max").
    # @param x_pos The x position in the parent widget.
    # @param width The width of the widget.
    # @param height The height of the widget.
    #
    def __init__(self, parent, settings, default_power, on_off_state, buttons, x_pos, width, height):
        QCubeChannel.__init__(self, parent, settings, default_power, on_off_state, buttons, x_pos, width, height)

    ## uiUpdate
    #
    # Open the shutter (if necessary) and call parent uiUpdate method.
    #
    def uiUpdate(self):
        self.shutter(self.amOn())
        QCubeChannel.uiUpdate(self)

    ## update
    #
    # Open the shutter (if necessary) and call parent update method.
    #
    # @param on True/False
    #
    def update(self, on):
        self.shutter(on)
        QCubeChannel.update(self, on)

## QNIChannel
#
# QChannel specialized for National Instruments control.
#
class QNIChannel(QChannel):

    ## __init__
    #
    # @param parent The PyQt parent of this widget.
    # @param settings The settings object associated with the channel.
    # @param on_off_state Is the channel on or off.
    # @param x_pos The x position in the parent widget.
    # @param width The width of the widget.
    # @param height The height of the widget.
    #
    def __init__(self, parent, settings, on_off_state, x_pos, width, height):
        QChannel.__init__(self, parent, settings, 1.0, x_pos, width, height)

        # power on/off radio button
        self.channel_frame.on_off_button = QtGui.QRadioButton(self.channel_frame)
        self.channel_frame.on_off_button.setGeometry(18, height - 24, 18, 18)
        if on_off_state:
            self.channel_frame.on_off_button.setChecked(True)
        else:
            self.channel_frame.on_off_button.setChecked(False)

        # connect signals
        self.channel_frame.on_off_button.clicked.connect(self.onOffChange)

        self.show()

    ## uiUpdate
    #
    # Put a request in the command queue to open/close the shutter.
    #
    def uiUpdate(self):
        self.cmd_queue.addRequest(self.amOn(),
                                  self.channel_settings.ni_board,
                                  self.channel_settings.ao_channel)

    ## update
    #
    # Tell the command queue to open/close the shutter immediately.
    #
    # @param on True/False.
    #
    def update(self, on):
        self.cmd_queue.addRequest(on,
                                  self.channel_settings.ni_board,
                                  self.channel_settings.ao_channel)

## QBasicChannel
#
# QChannel specialized for basic unsynchronized digital port control.
#
class QBasicChannel(QChannel):

    ## __init__
    #
    # @param parent The PyQt parent of this widget.
    # @param settings The settings object associated with the channel.
    # @param on_off_state Is the channel on or off.
    # @param x_pos The x position in the parent widget.
    # @param width The width of the widget.
    # @param height The height of the widget.
    #
    def __init__(self, parent, settings, on_off_state, x_pos, width, height):
        QChannel.__init__(self, parent, settings, 1.0, x_pos, width, height)

        # power on/off radio button
        self.channel_frame.on_off_button = QtGui.QRadioButton(self.channel_frame)
        self.channel_frame.on_off_button.setGeometry(18, height - 24, 18, 18)
        if on_off_state:
            self.channel_frame.on_off_button.setChecked(True)
        else:
            self.channel_frame.on_off_button.setChecked(False)

        # connect signals
        #self.connect(self.channel_frame.on_off_button, QtCore.SIGNAL("clicked()"),
        #             self.onOffChange)
        self.channel_frame.on_off_button.clicked.connect(self.onOffChange)

        self.show()

    ## uiUpdate
    #
    # Open/close the shutter as necessary.
    #
    def uiUpdate(self):
        self.shutter(self.amOn())

    ## update
    #
    # @param on True/False open/close the shutter.
    #
    def update(self, on):
        if (not self.filming_on):
            self.shutter(on)


## QFilterWheelChannel
#
# QChannel specialized for filter wheel control. This is assumed to also have a mechanical shutter.
# This channel displays in units of filter wheel position + 1. The filter wheel position is zero indexed.
#
class QFilterWheelChannel(QAdjustableChannel):

    ## __init__
    #
    # @param parent The PyQt parent of this widget.
    # @param settings The settings object associated with the channel.
    # @param default_power The initial amplitude of the channel.
    # @param on_off_state Is the channel on or off.
    # @param buttons An array of buttons for the channel (such as "Low" and "Max").
    # @param x_pos The x position in the parent widget.
    # @param width The width of the widget.
    # @param height The height of the widget.
    #
    def __init__(self, parent, settings, default_power, on_off_state, buttons, x_pos, width, height):
        QAdjustableChannel.__init__(self, parent, settings, default_power, on_off_state, buttons, x_pos, width, height)
        self.displayed_amplitude = self.current_amplitude + 1
        self.channel_frame.power_label.setText(str(self.displayed_amplitude))

    ## amplitudeChange
    #
    # @param amplitude The new amplitude.
    #
    def amplitudeChange(self, amplitude):
        self.current_amplitude = amplitude
        self.displayed_amplitude = amplitude + 1
        self.channel_frame.power_label.setText(str(self.displayed_amplitude))
        self.uiUpdate()

    ## uiUpdate
    #
    # Open/close the shutter as necessary.
    # Put a request into the command queue to update the filter wheel position.
    #
    def uiUpdate(self):
        self.shutter(self.amOn())
        self.cmd_queue.addRequest(self.amOn(), self.current_amplitude)

    ## update
    #
    # Open/close the shutter.
    # Tell the command queue to update the shutter position.
    def update(self, on):
        self.shutter(on)
        self.cmd_queue.setAmplitude(on, self.current_amplitude)


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
