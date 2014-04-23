#!/usr/bin/python
#
## @file
#
# This file contains hardware classes that interface with data acquistion cards.
#
# Hazen 04/14
#

from PyQt4 import QtCore

import illumination.hardwareModule as hardwareModule


## Daq
#
# The base class for data acquisition cards.
#
class Daq(hardwareModule.HardwareModule):

    ## __init__
    #
    # @param parameters A XML object containing initial parameters.
    # @param parent The PyQt parent of this object.
    #
    def __init__(self, parameters, parent):
        hardwareModule.HardwareModule.__init__(self, parameters, parent)

        self.analog_data = []
        self.analog_settings = {}
        self.digital_data = []
        self.digital_settings = {}
        self.shutter_settings = {}

    ## analogAddChannel
    #
    # @param channel_id The channel id.
    # @param channel_data The shutter data for this channel.
    #
    def analogAddChannel(self, channel_id, channel_data):
        self.analog_data.append([self.analog_settings[channel_id].channel, channel_data])

    ## analogOff
    #
    # Sets the analog voltage to the minimum.
    #
    # @param channel_id The channel id.
    #
    def analogOff(self, channel_id):
        pass

    ## analogOn
    #
    # Sets the analog voltage to the maximum.
    #
    # @param channel_id The channel id.
    #
    def analogOn(self, channel_id):
        pass

    ## digitalAddChannel
    #
    # @param channel_id The channel id.
    # @param channel_data The shutter data for this channel.
    #
    def digitalAddChannel(self, channel_id, channel_data):
        self.digital_data.append([self.digital_settings[channel_id].channel, channel_data])

    ## digitalOff
    #
    # Sets the digital line to 0.
    #
    # @param channel_id The channel id.
    #
    def digitalOff(self, channel_id):
        pass

    ## digitalOn
    #
    # Sets the digital line to 1.
    #
    # @param channel_id The channel id.
    #
    def digitalOn(self, channel_id):
        pass

    ## initialize
    #
    # This is called by each of the channels that wants to use this module.
    #
    # @param interface Interface type (from the perspective of the channel).
    # @param channel_id The channel id, this needs to be unique.
    # @param parameters A parameters object for this channel.
    #
    def initialize(self, interface, channel_id, parameters):
        if (interface == "analog_modulation"):
            self.analog_settings[channel_id] = parameters
        elif (interface == "digital_modulation"):
            self.digital_settings[channel_id] = parameters
        elif (interface == "mechanical_shutter"):
            self.shutter_settings[channel_id] = parameters

    ## powerToVoltage
    #
    # Convert a power (0.0 - 1.0) to the appropriate voltage based on channel settings.
    #
    # @param channel_id The channel id.
    # @param power The power (0.0 - 1.0)
    #
    # @return The voltage the corresponds to this power.
    #
    def powerToVoltage(self, channel_id, power):
        minv = self.analog_settings[channel_id].min_voltage
        maxv = self.analog_settings[channel_id].max_voltage
        diff = maxv - minv
        return diff * (power - minv)
    
    ## shutterOff
    #
    # Sets the shutter digital line to 0.
    #
    # @param channel_id The channel id.
    #
    def shutterOff(self, channel_id):
        pass

    ## digitalOn
    #
    # Sets the shutter digital line to 1.
    #
    # @param channel_id The channel id.
    #
    def shutterOn(self, channel_id):
        pass

    ## stopFilm
    #
    # Called at the end of filming (when shutters are active).
    #
    def stopFilm(self):
        hardwareModule.HardwareModule.stopFilm(self)
        self.analog_data = []
        self.digital_data = []


## NoneDaq
#
# Daq card emulation.
#
class NoneDaq(Daq):

    ## __init__
    #
    # @param parameters A XML object containing initial parameters.
    # @param parent The PyQt parent of this object.
    #
    def __init__(self, parameters, parent):
        Daq.__init__(self, parameters, parent)


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
