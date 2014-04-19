#!/usr/bin/python
#
## @file
#
# This file contains the Channel class.
#
# Hazen 04/14
#

from PyQt4 import QtCore

import illumination.illuminationChannelUI as illuminationChannelUI

## Channel
#
# This class is responsible for orchestrating the behaviour of a
# a single channel.
#
class Channel(QtCore.QObject):

    ## __init__
    #
    # @param channel A channelXML object describing the channel.
    # @param parameters A parameters XML object.
    # @param hardware_modules An array of hardware module objects.
    # @param channels_box The UI group box where the channels will be drawn.
    #
    @hdebug.debug
    def __init__(self, channel, parameters, hardware_modules, channels_box):
        QtCore.QObject.__init__(self, channels_box)

        self.am_on = False
        self.channel_number = channel.channel_id
        self.channel_ui = False
        self.current_power = 0
        self.display_normalized = False
        self.max_amplitude = 1.0
        self.name = channel.description
        self.parameters = False
        self.shutter_data = []
        self.used_for_film = False
        self.was_on = False

        for [var, name] in [[self.amplitude_modulation, "amplitude_modulation"],
                            [self.analog_modulation, "analog_modulation"],
                            [self.digital_modulation, "digital_modulation"],
                            [self.mechanical_shutter, "mechanical_shutter"]]:
            if hasattr(channel, name):
                temp = getattr(channel, name)
                var = hardware_modules[temp.uses]
                var.initialize(self.channel_number, temp.parameters)
            else:
                var = False

        if self.amplitude_modulation:
            self.display_normalized = channel.amplitude_modulation.display_normalized
            self.max_amplitude = self.amplitude_modulation.getAmplitude(self.channel_number)
            self.channel_ui = illuminationChannelUI.ChannelUIAdjustable(self.name,
                                                                        channel.color,
                                                                        parameters,
                                                                        self.max_amplitude,
                                                                        channels_box)
        else:
            self.channel_ui = illuminationChannelUI.ChannelUI(self.name,
                                                              channel.color,
                                                              parameters,
                                                              channels_box)

        self.channel_ui.onOffChange.connect(self.handleOnOffChange)
        self.channel_ui.powerChange.connect(self.handleSetPower)

    ## getAmplitude
    #
    # @return The current amplitude of the channel (as a string).
    #
    def getAmplitude(self):
        return self.channel_ui.getAmplitude()

    ## getHeight
    #
    # @return The height of the channel UI element.
    #
    def getHeight(self):
        return self.channel_ui.height()

    ## getWidth
    #
    # @return The width of the channel UI element.
    def getWidth(self):
        return self.channel_ui.width()

    ## getName
    #
    # @return The name of the channel.
    #
    def getName(self):
        return self.name

    ## handleOnOffChange
    #
    # Handles a request to turn the channel on / off. These all
    # come from the UI.
    #
    # @param on True/False on/off.
    #
    def handleOnOffChange(self, on):
        self.am_on = on
        if self.am_on:
            if self.amplitude_modulation:
                self.handleSetPower(self.current_power)
        
            if self.analog_modulation:
                self.analog_modulation.turnOn(self.channel_number)

            if self.digital_modulation:
                self.digital_modulation.turnOn(self.channel_number)

            if self.mechanical_shutter:
                self.mechanical_shutter.openShutter(self.channel_number)

        else:
            if self.amplitude_modulation:
                self.handleSetPower(0)
        
            if self.analog_modulation:
                self.analog_modulation.turnOff(self.channel_number)

            if self.digital_modulation:
                self.digital_modulation.turnOff(self.channel_number)

            if self.mechanical_shutter:
                self.mechanical_shutter.closeShutter(self.channel_number)

    ## handleSetPower
    #
    # Handles requests to set the current channel power to a new value.
    # These all come from the UI. The current power is always whatever
    # the current value of the slider is.
    #
    # @param new_power The new channel power setting.
    #
    def handleSetPower(self, new_power):
        if self.display_normalized:
            power_string = "{0:.4f}".format(float(new_power)/self.max_amplitude)
        else:
            power_string = "{0:d}".format(new_power)
            self.channel_ui.updatePowerText(power_string)

        if self.am_on:
            self.current_power = new_power
            if self.amplitude_modulation:
                self.amplitude_modulation.setPower(self.channel_number, new_power)

            if self.mechanical_shutter:
                if (new_power == 0):
                    self.mechanical_shutter.closeShutter(self.channel_number)
                else:
                    self.mechanical_shutter.openShutter(self.channel_number)

    ## newParameters
    #
    # @param parameters A parameters XML object.
    #
    def newParameters(self, parameters):
        if self.parameters:
            self.parameters.shutter_data[self.channel_number] = self.shutter_data

        self.parameters = parameters
        self.shutter_data = self.parameters.shutter_data[self.channel_number]
        self.channel_ui.newParameters(self.parameters, self.channel_number)

    ## newShutters
    #
    # @param shutter_data A array containing the shutter data.
    #
    def newShutters(self, shutter_data):
        self.shutter_data = shutter_data
        self.used_for_film = False
        if any((y > 0.0) for y in self.shutter_data):
            self.used_for_film = True

        if self.analog_modulation:
            for i in len(self.shutter_data):
                self.shutter_data[i] = self.analog_modulation.powerToVoltage(self.channel_number, self.shutter_data[i])

    ## remoteIncPower
    #
    # Handles power increment requests that come from outside of the illumination UI.
    # This is "bounced" off the UI slider, for range checking.
    #
    # @param power_inc The channel power increment (0.0 - 1.0).
    #
    def remoteIncPower(self, power_inc):
        self.channel_ui.remoteIncPower(round(int(new_power * self.max_amplitude)))

    ## remoteSetPower
    #
    # Handles power requests that come from outside of the illumination UI.
    # This is "bounced" off the UI slider, for range checking.
    #
    # @param new_power The channel power setting (0.0 - 1.0).
    #
    def remoteSetPower(self, new_power):
        self.channel_ui.remoteSetPower(round(int(new_power * self.max_amplitude)))

    ## setPosition
    #
    # @param x The x location of the channel UI.
    # @param y The y location of the channel UI.
    #
    # @return The width of the channel UI.
    #
    def setPosition(self, x, y):
        self.channel_ui.move(x, y)
        return self.channel_ui.width()

    ## startFilm
    #
    # Called at the start of filming to get the channel setup.
    #
    def startFilm(self):
        self.was_on = self.am_on

        if self.analog_modulation:
            self.analog_modulation.turnOff(self.channel_number)
            self.analog_modulation.addChannel(self.channel_number, self.shutter_data)

        if self.digital_modulation:
            self.digital_modulation.turnOff(self.channel_number)
            self.digital_modulation.addChannel(self.channel_number, self.shutter_data)

        if not self.used_for_film:
            self.channel_ui.disableChannel()

    ## stopFilm
    #
    # Called at the end of filming to reset things.
    #
    def stopFilm(self):
        if not self.used_for_film:
            self.channel_ui.enableChannel()
        self.channel_ui.setOnOff(self.was_on)

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
