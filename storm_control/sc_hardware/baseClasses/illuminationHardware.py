#!/usr/bin/env python
"""
This file contains the base illumination hardware class as well
as a buffered variant. Any hardware that will be used for
illumination control should be a sub-class of one of these
classes.

Hazen 04/14
"""

from PyQt5 import QtCore


def removeChannelDuplicates(queue, channel):
    """
    Remove settings that apply to the current channel. This way
    when you move the slider and generate 100 events only the last
    one gets acted on, but pending events for other channels are not lost.
    """
    final_queue = []
    for item in queue:
        if (item[0] == channel):
            continue
        final_queue.append(item)
    return final_queue


class IlluminationHardware(object):
    """
    The base class for illumination hardware.

    This class is responsible for communication between a channel
    and a particular piece of hardware.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.filming = False
        self.is_buffered = False
        self.working = True

    def cleanup(self):
        """
        Called when the program closes to clean up.
        """
        pass

    def getStatus(self):
        """
        return True/False if the device this module talks to is working properly.
        """
        return self.working

    def initialize(self, interface, channel_id, parameters):
        """
        This is called by each of the channels that wants to use this module.
        """
        pass

    def isBuffered(self):
        """
        If the module is buffered (i.e. a QThread) then we'll need to start
        it after we instantiate it.
        """
        return self.is_buffered

    def startFilm(self, seconds_per_frame, oversampling):
        """
        Called at the start of filming (when shutters are active).
        """
        self.filming = True

    def stopFilm(self):
        """
        Called at the end of filming (when shutters are active).
        """
        self.filming = False


class AmplitudeModulation(IlluminationHardware):
    """
    The base class for hardware modules that deal with amplitude controlling hardware.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.channel_parameters = {}

    def amplitudeOff(self, channel_id):
        """
        Called when the module should turn off a channel.
        """
        pass

    def amplitudeOn(self, channel_id, amplitude):
        """
        Called when the module should turn on a channel.
        """
        pass

    def getMaxAmplitude(self, channel_id):
        return self.channel_parameters[channel_id].maximum

    def getMinAmplitude(self, channel_id):
        params = self.channel_parameters[channel_id]
        if (hasattr(params, "minimum")):
            return params.minimum
        else:
            return 0

    def initialize(self, interface, channel_id, parameters):
        self.channel_parameters[channel_id] = parameters

    def setAmplitude(self, channel, amplitude):
        pass


class BufferedAmplitudeModulation(QtCore.QThread, AmplitudeModulation):
    """
    The base class for buffered amplitude hardware modules.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)
        
        self.command_buffer = []
        self.buffer_mutex = QtCore.QMutex()
        self.device_mutex = QtCore.QMutex()
        self.is_buffered = True
        self.running = True

    def cleanup(self):
        """
        Stop the command queue thread.
        """
        self.running = False
        self.wait()

    def deviceSetAmplitude(self, channel, amplitude):
        self.device_mutex.lock()
        print("deviceSetAmplitude should have been over-ridden..")
        self.device_mutex.unlock()

    def run(self):
        """
        Pops the most recent command request off the queue, removes
        any duplicates of this request from the queue and executes
        the request. Sleeps for 10ms between queue checks.
        """
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

    def setAmplitude(self, channel, amplitude):
        """
        Put a request in the queue.
        """
        self.buffer_mutex.lock()
        self.command_buffer.append([channel, amplitude])
        self.buffer_mutex.unlock()


class DaqModulation(IlluminationHardware):
    """
    The base class for data acquisition cards.
    """
    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.analog_data = []
        self.analog_settings = {}
        self.digital_data = []
        self.digital_settings = {}
        self.shutter_settings = {}

    def analogAddChannel(self, channel_id, channel_data):
        self.analog_data.append([self.analog_settings[channel_id].board,
                                 self.analog_settings[channel_id].channel,
                                 channel_data])

    def analogOff(self, channel_id):
        """
        Sets the analog voltage to the minimum.
        """
        pass

    def analogOn(self, channel_id):
        """
        Sets the analog voltage to the maximum.
        """
        pass

    def digitalAddChannel(self, channel_id, channel_data):
        self.digital_data.append([self.digital_settings[channel_id].board,
                                  self.digital_settings[channel_id].channel,
                                  channel_data])

    def digitalOff(self, channel_id):
        """
        Sets the digital line to 0.
        """
        pass

    def digitalOn(self, channel_id):
        """
        Sets the digital line to 1.
        """
        pass

    def initialize(self, interface, channel_id, parameters):
        """
        This is called by each of the channels that wants to use this module.
        """
        if (interface == "analog_modulation"):
            self.analog_settings[channel_id] = parameters
        elif (interface == "digital_modulation"):
            self.digital_settings[channel_id] = parameters
        elif (interface == "mechanical_shutter"):
            self.shutter_settings[channel_id] = parameters

    def powerToVoltage(self, channel_id, power):
        """
        Convert a power (0.0 - 1.0) to the appropriate voltage based on channel settings.
        """
        minv = self.analog_settings[channel_id].min_voltage
        maxv = self.analog_settings[channel_id].max_voltage
        diff = maxv - minv
        return diff * (power - minv)
    
    def shutterOff(self, channel_id):
        """
        Sets the shutter digital line to 0.
        """
        pass

    def shutterOn(self, channel_id):
        """
        Sets the shutter digital line to 1.
        """
        pass

    def stopFilm(self):
        """
        Called at the end of filming (when shutters are active).
        """
        super().stopFilm()
        self.analog_data = []
        self.digital_data = []

    def waveformToVoltage(self, channel_id, waveform):
        """
        Convert a waveform (0.0 - 1.0 numpy array) to correct voltage.
        """
        minv = self.analog_settings[channel_id].min_voltage
        maxv = self.analog_settings[channel_id].max_voltage
        diff = maxv - minv
        return diff * (waveform - minv)


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
