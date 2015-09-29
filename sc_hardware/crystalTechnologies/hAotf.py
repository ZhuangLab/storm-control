#!/usr/bin/python
#
## @file
#
# This file contains hardware classes that interface the
# Crystal Technologies AOTF to HAL.
#
# Hazen 04/14
#

import sc_hardware.baseClasses.illuminationHardware as illuminationHardware


## CrystalTechAOTF
#
# Crystal Technologies AOTF.
#
class CrystalTechAOTF(illuminationHardware.BufferedAmplitudeModulation):

    ## __init__
    #
    # @param parameters A XML object containing initial parameters.
    # @param parent The PyQt parent of this object.
    #
    def __init__(self, parameters, parent):
        illuminationHardware.BufferedAmplitudeModulation.__init__(self, parameters, parent)

        self.amplitude_on = {}

        if not (self.aotf.getStatus()):
            self.working = False

        if self.working:
            self.use_fsk = parameters.use_fsk
            if self.use_fsk:
                self.aotf.analogModulationOn()
            else:
                self.aotf.analogModulationOff()

            if hasattr(parameters, "fsk_mode"):
                self.fsk_mode = parameters.fsk_mode
            else:
                self.fsk_mode = 1

    ## amplitudeOff
    #
    # Called when the module should turn off a channel.
    #
    # @param channel_id The channel id.
    #
    def amplitudeOff(self, channel_id):
        self.amplitude_on[channel_id] = False
        aotf_channel = self.channel_parameters[channel_id].channel
        self.device_mutex.lock()
        self.aotf.setAmplitude(aotf_channel, 0)
        self.device_mutex.unlock()

    ## amplitudeOn
    #
    # Called when the module should turn on a channel.
    #
    # @param channel_id The channel id.
    # @param amplitude The channel amplitude.
    #
    def amplitudeOn(self, channel_id, amplitude):
        self.amplitude_on[channel_id] = True
        self.setAmplitude(channel_id, amplitude)

    ## cleanup
    #
    # Called when the program closes to clean up.
    #
    def cleanup(self):
        illuminationHardware.BufferedAmplitudeModulation.cleanup(self)
        self.aotf.shutDown()

    ## deviceSetAmplitude
    #
    # @param channel_id The channel.
    # @param amplitude The channel amplitude.
    #
    def deviceSetAmplitude(self, channel_id, amplitude):
        if self.amplitude_on[channel_id]:
            aotf_channel = self.channel_parameters[channel_id].channel
            self.device_mutex.lock()
            self.aotf.setAmplitude(aotf_channel, amplitude)
            self.device_mutex.unlock()

    ## initialize
    #
    # This is called by each of the channels that wants to use this module.
    #
    # @param interface Interface type (from the perspective of the channel).
    # @param channel_id The channel id.
    # @param parameters A parameters object for this channel.
    #
    def initialize(self, interface, channel_id, parameters):
        illuminationHardware.BufferedAmplitudeModulation.initialize(self, interface, channel_id, parameters)
        self.amplitude_on[channel_id] = False

        aotf_channel = self.channel_parameters[channel_id].channel
        off_frequency = self.channel_parameters[channel_id].off_frequency
        on_frequency = self.channel_parameters[channel_id].on_frequency

        if self.working:

            if self.use_fsk:
                frequencies = [off_frequency, on_frequency, off_frequency, off_frequency]
            else:
                frequencies = [on_frequency, off_frequency, off_frequency, off_frequency]

            self.device_mutex.lock()
            self.aotf.setFrequencies(aotf_channel, frequencies)
            if self.use_fsk:
                self.aotf.fskOn(aotf_channel, self.fsk_mode)
            else:
                self.aotf.fskOff(aotf_channel)
            self.device_mutex.unlock()


## CrystalTechAOTF32bit
#
# Crystal Technologies (32 bit) AOTF.
#
class CrystalTechAOTF32Bit(CrystalTechAOTF):

    ## __init__
    #
    # @param parameters A XML object containing initial parameters.
    # @param parent The PyQt parent of this object.
    #
    def __init__(self, parameters, parent):

        import sc_hardware.crystalTechnologies.AOTF as AOTF
        self.aotf = AOTF.AOTF()

        CrystalTechAOTF.__init__(self, parameters, parent)


## CrystalTechAOTF64bit
#
# Crystal Technologies (64 bit) AOTF.
#
class CrystalTechAOTF64Bit(CrystalTechAOTF):

    ## __init__
    #
    # @param parameters A XML object containing initial parameters.
    # @param parent The PyQt parent of this object.
    #
    def __init__(self, parameters, parent):

        import sc_hardware.crystalTechnologies.AOTF as AOTF
        self.aotf = AOTF.AOTF64Bit()

        CrystalTechAOTF.__init__(self, parameters, parent)


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
