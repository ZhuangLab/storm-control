#!/usr/bin/python
#
## @file
#
# Gooch and Housego AOTF control.
#
# Hazen 02/14
#

import halLib.RS232 as RS232

import time

## AOTF
#
# Class for controlling a AA Opto-electronics AOTF using RS-232 communication.
#
class AOTF(RS232.RS232):

    ## __init__
    #
    # Create the control object, connect to the AOTF at the specified COM port.
    #
    # @param port The COM port that the AOTF is connected to.
    #
    def __init__(self, port = "COM8"):
        self.active_channel = False
        self.channels = []
        self.number_channels = 8
        try:
            # open port
            RS232.RS232.__init__(self, port, None, 9600, "\r", 0.05)

            # verify that we can talk to the AOTF
            assert not(self.commWithResp("st") == None)

        except:
            self.live = 0
            print "Failed to connect to the Gooch and Housego AOTF at port", port

    ## analogModulationOff
    #
    # Turns off analog modulation of the AOTF.
    #
    def analogModulationOff(self):
        for channel in self.channels:
            self.setActiveChannel(channel)
            self.commWithResp("on")

    ## analogModulationOn
    #
    # Turns on analog modulation of the AOTF.
    def analogModulationOn(self):
        for i in range(self.number_channels):
            self.setActiveChannel(i+1)
            self.commWithResp("mod")

    ## channelOnOff
    #
    # Turn the specified channel on or off.
    #
    # @param channel The channel to turn on or off.
    # @param on True/False turn the channel on/off.
    #
    def channelOnOff(self, channel, on):
        pass

    ## getStatus
    #
    # Get whether or not the class is actually connected to the AOTF.
    #
    def getStatus(self):
        return self.live

    ## setActiveChannel
    #
    # @param channel The channel to make active.
    #
    def setActiveChannel(self, channel):
        if not (channel == self.active_channel):
            self.active_channel = channel
            self.commWithResp("ch" + str(channel))

    ## setAmplitude
    #
    # Set the amplitude of a channel of the AOTF.
    #
    # @param channel The channel to set amplitude of.
    # @param amplitude The desired amplitude.
    #
    def setAmplitude(self, channel, amplitude):
        assert channel > 0, "setAmplitude: channel out of range " + str(channel)
        assert channel <= 8, "setAmplitude: channel out of range " + str(channel)
        if not (channel in self.channels):
            self.channels.append(channel)
        self.setActiveChannel(channel)
        self.commWithResp("am " + str(amplitude))

    ## setFrequency
    #
    # Set the frequencyt of a channel of the AOTF.
    #
    # @param channel The channel to set the frequency of.
    # @param frequency The desired frequency.
    #
    def setFrequency(self, channel, frequency):
        assert channel > 0, "setFrequency: channel out of range " + str(channel)
        assert channel <= 8, "setFrequency: channel out of range " + str(channel) 
        self.setActiveChannel(channel)
        cmd = "fr " + "{0:.3f}".format(frequency)
        self.commWithResp(cmd)

    ## shutDown
    #
    # Reset the AOTF frequencies and disconnect from the AOTF.
    #
    def shutdown(self):
        # reset frequencies in case the next user is using the M. Bates Labview interface.
        for i, frequency in enumerate(self.frequencies):
            self.setFrequency(i, frequency)
        RS232.RS232.shutdown()

#
# Testing
#

if __name__ == "__main__":
    aotf = AOTF()
    aotf.setAmplitude(1, 100)
    aotf.setFrequency(1, 62.0)
    print aotf.commWithResp("st")
    aotf.shutDown()


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

