#!/usr/bin/python
#
## @file
#
# This file contains the base illumination hardware class as well
# as a buffered variant. Any hardware that will be used for
# illumination control should be a sub-class of one of these
# classes.
#
# Hazen 04/14
#

from PyQt4 import QtCore

#
# Helper functions.
#

## removeChannelDuplicates
#
# Remove settings that apply to the current channel. This way
# when you move the slider and generate 100 events only the last
# one gets acted on, but pending events for other channels are not lost.
#
# @param queue A python array of [on, channel, amplitude].
# @param channel All items in queue that have this channel value will be removed.
#
# @return The original array with all items from channel removed.
#
def removeChannelDuplicates(queue, channel):
    final_queue = []
    for item in queue:
        if (item[0] == channel):
            continue
        final_queue.append(item)
    return final_queue


#
# Base Class.
#

## IlluminationHardware
#
# The base class for illumination hardware.
#
# This class is responsible for communication between a channel
# and a particular piece of hardware.
#
class IlluminationHardware(object):

    ## __init__
    #
    # @param parameters A XML object containing initial parameters.
    # @param parent The PyQt parent of this object.
    #
    def __init__(self, parameters, parent):

        self.filming = False
        self.is_buffered = False
        self.working = True

    ## cleanup
    #
    # Called when the program closes to clean up.
    #
    def cleanup(self):
        pass

    ## getStatus
    #
    # @return True/False if the device this module talks to is working properly.
    #
    def getStatus(self):
        return self.working

    ## initialize
    #
    # This is called by each of the channels that wants to use this module.
    #
    # @param interface Interface type (from the perspective of the channel).
    # @param channel_id The channel id.
    # @param parameters A parameters object for this channel.
    #
    def initialize(self, interface, channel_id, parameters):
        pass

    ## isBuffered
    #
    # If the module is buffered (i.e. a QThread) then we'll need to start
    # it after we instantiate it.
    #
    # @return True/False if this module is buffered.
    #
    def isBuffered(self):
        return self.is_buffered

    ## startFilm
    #
    # Called at the start of filming (when shutters are active).
    #
    # @param seconds_per_frame How many seconds it takes to acquire each frame.
    # @param oversampling The number of values in the shutter waveform per frame.
    #
    def startFilm(self, seconds_per_frame, oversampling):
        self.filming = True

    ## stopFilm
    #
    # Called at the end of filming (when shutters are active).
    #
    def stopFilm(self):
        self.filming = False


#
# Sub classes.
#

## AmplitudeModulation
#
# The base class for hardware modules that deal with amplitude controlling hardware.
#
class AmplitudeModulation(IlluminationHardware):

    ## __init__
    #
    # @param parameters A XML object containing initial parameters.
    # @param parent The PyQt parent of this object.
    #
    def __init__(self, parameters, parent):
        IlluminationHardware.__init__(self, parameters, parent)

        self.channel_parameters = {}

    ## amplitudeOff
    #
    # Called when the module should turn off a channel.
    #
    # @param channel_id The channel id.
    #
    def amplitudeOff(self, channel_id):
        pass

    ## amplitudeOn
    #
    # Called when the module should turn on a channel.
    #
    # @param channel_id The channel id.
    # @param amplitude The channel amplitude.
    #
    def amplitudeOn(self, channel_id, amplitude):
        pass

    ## getMaxAmplitude
    #
    # @param channel_id The channel id.
    #
    # @return The maximum amplitude for this channel.
    #
    def getMaxAmplitude(self, channel_id):
        return self.channel_parameters[channel_id].maximum

    ## getMinAmplitude
    #
    # @param channel_id The channel id.
    #
    # @return The minimum amplitude for this channel.
    #
    def getMinAmplitude(self, channel_id):
        params = self.channel_parameters[channel_id]
        if (hasattr(params, "minimum")):
            return params.minimum
        else:
            return 0

    ## initialize
    #
    # This is called by each of the channels that wants to use this module.
    #
    # @param interface Interface type (from the perspective of the channel).
    # @param channel_id The channel id.
    # @param parameters A parameters object for this channel.
    #
    def initialize(self, interface, channel_id, parameters):
        self.channel_parameters[channel_id] = parameters

    ## setAmplitude
    #
    # @param channel The channel.
    # @param amplitude The channel amplitude.
    #
    def setAmplitude(self, channel, amplitude):
        pass


## BufferedAmplitudeModulation
#
# The base class for buffered amplitude hardware modules.
#
class BufferedAmplitudeModulation(QtCore.QThread, AmplitudeModulation):

    ## __init__
    #
    # @param parameters A XML object containing initial parameters.
    # @param parent The PyQt parent of this object.
    #
    def __init__(self, parameters, parent):
        QtCore.QThread.__init__(self, parent)
        AmplitudeModulation.__init__(self, parameters, parent)
        
        self.command_buffer = []
        self.buffer_mutex = QtCore.QMutex()
        self.device_mutex = QtCore.QMutex()
        self.is_buffered = True
        self.running = True

    ## cleanup
    #
    # Stop the command queue thread.
    #
    def cleanup(self):
        self.running = False
        self.wait()

    ## deviceSetAmplitude
    #
    # @param channel The channel.
    # @param amplitude The channel amplitude.
    #
    def deviceSetAmplitude(self, channel, amplitude):
        self.device_mutex.lock()
        print "deviceSetAmplitude should have been over-ridden.."
        self.device_mutex.unlock()

    ## run
    #
    # Pops the most recent command request off the queue, removes
    # any duplicates of this request from the queue and executes
    # the request. Sleeps for 10ms between queue checks.
    #
    def run(self):
        while (self.running):
            self.buffer_mutex.lock()
            if (len(self.command_buffer) > 0):
                [channel, amplitude] = self.command_buffer.pop()
                self.command_buffer = removeChannelDuplicates(self.command_buffer, channel)
                self.buffer_mutex.unlock()
                self.deviceSetAmplitude(channel, amplitude)
            else:
                self.buffer_mutex.unlock()
            self.msleep(10)

    ## setAmplitude
    #
    # Put a request in the queue.
    #
    # @param channel The channel.
    # @param amplitude The channel amplitude.
    #
    def setAmplitude(self, channel, amplitude):
        self.buffer_mutex.lock()
        self.command_buffer.append([channel, amplitude])
        self.buffer_mutex.unlock()


## DaqModulation
#
# The base class for data acquisition cards.
#
class DaqModulation(IlluminationHardware):

    ## __init__
    #
    # @param parameters A XML object containing initial parameters.
    # @param parent The PyQt parent of this object.
    #
    def __init__(self, parameters, parent):
        IlluminationHardware.__init__(self, parameters, parent)

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
        IlluminationHardware.stopFilm(self)
        self.analog_data = []
        self.digital_data = []


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
