#!/usr/bin/python
#
## @file
#
# AA Opto-electronics AOTF control.
#
# This class saves the set frequency for each channel
# to make it easier to implement a frequency offset
# function.
#
# Hazen 12/10
#

import sc_hardware.serial.RS232 as RS232
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
    def __init__(self, port = "COM2"):
        self.channel = 1
        self.frequencies = []
        self.on_off = []
        for i in range(8):
            self.frequencies.append(74.0)
            self.on_off.append(False)
        try:
            # open port
            RS232.RS232.__init__(self, port, None, 19200, "\r", 0.05)

            # verify that we can talk to the AOTF
            assert not(self.commWithResp("q") == None)

            # switch to digital (RS-232) modulation
            self.analogModulationOff()
        except:
            self.live = 0
            print "Failed to connect to the AA AOTF at port", port

    ## analogModulationOff
    #
    # Turns off analog modulation of the AOTF.
    #
    def analogModulationOff(self):
        self.commWithResp("I0")

    ## analogModulationOn
    #
    # Turns on analog modulation of the AOTF.
    def analogModulationOn(self):
        self.commWithResp("I1")

    ## channelOnOff
    #
    # Turn the specified channel on or off.
    #
    # @param channel The channel to turn on or off.
    # @param on True/False turn the channel on/off.
    #
    def channelOnOff(self, channel, on):
        if on:
            if (not self.on_off[channel]):
                cmd = "L" + str(channel) + "O1"
                self.commWithResp(cmd)
                self.on_off[channel] = True
        else:
            if (self.on_off[channel]):
                cmd = "L" + str(channel) + "O0"
                self.commWithResp(cmd)
                self.on_off[channel] = False

    ## getInfo
    #
    # Get info from the AOTF.
    #
    def getInfo(self):
        print "type:", self.commWithResp("q")
        print "status:"
        print self.commWithResp("s")

    ## getStatus
    #
    # Get whether or not the class is actually connected to the AOTF.
    #
    def getStatus(self):
        return self.live

    ## offsetFrequency
    #
    # Set the frequence offset of a channel. This was an attempt to get better
    # modulation out of a AOTF that does not have very good modulation.
    #
    # @param channel The channel to offset the frequency of.
    # @param freq_offset The amount of frequency offset.
    #
    def offsetFrequency(self, channel, freq_offset):
        cmd = "L" + str(channel) + "F{0:.3f}".format(self.frequencies[channel] + freq_offset)
        self.commWithResp(cmd)

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
        cmd = "L" + str(channel) + "D{0:.2f}".format(amplitude)
#        cmd = "L" + str(channel) + "P" + str(amplitude)
        self.commWithResp(cmd)

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
        cmd = "L" + str(channel) + "F{0:.3f}".format(frequency)
        self.commWithResp(cmd)
        self.frequencies[channel] = frequency

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
    aotf.getInfo()
#    if 0:
#        for i in range(8):
#            aotf.setAmplitude(i+1, 0.0)
#            aotf.setFrequency(i+1, 74.0)
#    if 1:
#        aotf.setAmplitude(2, 900)
#        aotf.setFrequency(2, 91.480)
#        aotf.setFrequency(2, 92.980)
#        aotf.channelOnOff(2, True)

#        aotf.setFrequency(2, 74.0)
#    aotf.getInfo()
    aotf.shutDown()
#    input()

#
# The MIT License
#
# Copyright (c) 2010 Zhuang Lab, Harvard University
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

