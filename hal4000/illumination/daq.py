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
        self.analog_data.append([self.analog_settings[channel_id].board,
                                 self.analog_settings[channel_id].channel,
                                 channel_data])

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
        self.digital_data.append([self.digital_settings[channel_id].board,
                                  self.digital_settings[channel_id].channel,
                                  channel_data])

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


## Nidaq
#
# National Instruments DAQ card.
#
class Nidaq(Daq):

    ## __init__
    #
    # @param parameters A XML object containing initial parameters.
    # @param parent The PyQt parent of this object.
    #
    def __init__(self, parameters, parent):
        Daq.__init__(self, parameters, parent)

        import nationalInstruments.nicontrol as nicontrol
        self.nicontrol = nicontrol

        self.ao_task = False
        self.ct_task = False
        self.do_task = False

        if (hasattr(parameters, "counter_board")):
            self.counter_board = parameters.counter_board
            self.counter_id = parameters.counter_id
            self.counter_trigger = parameters.counter_trigger
        else:
            self.counter_board = False
            self.counter_id = False
            self.counter_trigger = False

        # FIXME:
        #   Need a waveform_clock_board parameter and we need to fix
        #   nicontrol to respect this, otherwise we can only use one
        #   board for waveform output.
        if (hasattr(parameters, "waveform_clock")):
            self.waveform_clock = parameters.waveform_clock
        else:
            self.waveform_clock = False
    
    ## analogOff
    #
    # Sets the analog voltage to the minimum.
    #
    # @param channel_id The channel id.
    #
    def analogOff(self, channel_id):
        if not self.filming:
            self.nicontrol.setAnalogLine(self.analog_settings[channel_id].board,
                                         self.analog_settings[channel_id].channel,
                                         self.analog_settings[channel_id].min_voltage)

    ## analogOn
    #
    # Sets the analog voltage to the maximum.
    #
    # @param channel_id The channel id.
    #
    def analogOn(self, channel_id):
        if not self.filming:
            self.nicontrol.setAnalogLine(self.analog_settings[channel_id].board,
                                         self.analog_settings[channel_id].channel,
                                         self.analog_settings[channel_id].max_voltage)

    ## digitalOff
    #
    # Sets the digital line to 0.
    #
    # @param channel_id The channel id.
    #
    def digitalOff(self, channel_id):
        if not self.filming:
            self.nicontrol.setDigitalLine(self.digital_settings[channel_id].board,
                                          self.digital_settings[channel_id].channel,
                                          False)

    ## digitalOn
    #
    # Sets the digital line to 1.
    #
    # @param channel_id The channel id.
    #
    def digitalOn(self, channel_id):
        if not self.filming:
            self.nicontrol.setDigitalLine(self.digital_settings[channel_id].board,
                                          self.digital_settings[channel_id].channel,
                                          True)

    ## shutterOff
    #
    # Sets the shutter digital line to 0.
    #
    # @param channel_id The channel id.
    #
    def shutterOff(self, channel_id):
        self.nicontrol.setDigitalLine(self.shutter_settings[channel_id].board,
                                      self.shutter_settings[channel_id].channel,
                                      False)

    ## digitalOn
    #
    # Sets the shutter digital line to 1.
    #
    # @param channel_id The channel id.
    #
    def shutterOn(self, channel_id):
        self.nicontrol.setDigitalLine(self.shutter_settings[channel_id].board,
                                      self.shutter_settings[channel_id].channel,
                                      True)

    ## startFilm
    #
    # Called at the start of filming (when shutters are active).
    #
    # @param seconds_per_frame How many seconds it takes to acquire each frame.
    # @param oversampling The number of values in the shutter waveform per frame.
    #
    def startFilm(self, seconds_per_frame, oversampling):
        Daq.startFilm(self, seconds_per_frame, oversampling)

        # Calculate frequency. This is set slightly higher than the camere
        # frequency so that we are ready at the start of the next frame.
        frequency = (1.001 / seconds_per_frame) * float(oversampling)

        # Setup analog waveforms.
        if (len(self.analog_data) > 0):

            # Sort by board, channel.
            analog_data = sorted(self.analog_data, key = lambda x: (x[0], x[1]))

            # Create channels.
            self.ao_task = self.nicontrol.AnalogWaveformOutput(analog_data[0][0], analog_data[0][1])
            for i in range(len(analog_data) - 1):
                self.ao_task.addChannel(analog_data[i+1][0], analog_data[i+1][1])

            # Set waveforms.
            waveform = []
            for i in range(len(analog_data)):
                waveform += analog_data[i][2]

            self.ao_task.setWaveform(waveform, frequency, clock = self.waveform_clock)
        else:
            self.ao_task = False

        # Setup digital waveforms.
        if (len(self.digital_data) > 0):

            # Sort by board, channel.
            digital_data = sorted(self.digital_data, key = lambda x: (x[0], x[1]))

            # Create channels.
            self.do_task = self.nicontrol.DigitalWaveformOutput(digital_data[0][0], digital_data[0][1])
            for i in range(len(digital_data) - 1):
                self.do_task.addChannel(digital_data[i+1][0], digital_data[i+1][1])

            # Set waveforms.
            waveform = []
            for i in range(len(digital_data)):
                waveform += digital_data[i][2]

            self.do_task.setWaveform(waveform, frequency, clock = self.waveform_clock)
        else:
            self.do_task = False

        # Setup the counter.
        if self.counter_board:
            self.ct_task = self.nicontrol.CounterOutput(self.counter_board, 
                                                        self.counter_id,
                                                        frequency, 
                                                        0.5)
            self.ct_task.setCounter(oversampling)
            self.ct_task.setTrigger(self.counter_trigger)
        else:
            self.ct_task = False

        # Start tasks
        for task in [self.ct_task, self.ao_task, self.do_task]:
            if task:
                task.startTask()

    ## stopFilm
    #
    # Called at the end of filming (when shutters are active).
    #
    def stopFilm(self):
        Daq.stopFilm(self)
        for task in [self.ct_task, self.ao_task, self.do_task]:
            if task:
                task.stopTask()
                task.clearTask()


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
