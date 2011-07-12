#!/usr/bin/python
#
# Communicates with the Crystal Technologies AOTF (via USB).
#
# Hazen 2/09
#

from ctypes import *
import time

response_time = 0.05

# Load the AOTF driver library library.
aotf = cdll.LoadLibrary("C:\Program Files\Crystal Technology\AOTF Utilities\AotfLibrary\LegacyAotfLibrary\DLL\AotfLibrary")

instantiated = 0

# FIXME: I'd like for this class to make sure that the AOTF is closed
# For now, you have to make sure shutdown is called or the process will
# lock (or at least it will lock the DOS prompt).
class AOTF():
    def __init__(self):
        global instantiated
        self.live = 1
        if instantiated:
            print "Attempt to instantiate to AOTF communication classes."
            self.live = 0
        else:
            if self._aotfOpen():
                self.live = 1
                instantiated = 1
            else:
                print "Failed to connect to the AOTF, perhaps it is turned off?"
                self.live = 0
            
    def _aotfGetResp(self):
        if self.live:
            response = ""
            b_size = 100
            time.sleep(response_time)
            have_data = aotf.AotfIsReadDataAvailable(self.aotf_handle)
            while have_data:
                c_resp = create_string_buffer(b_size)
                c_read = c_uint(0)
                assert aotf.AotfRead(self.aotf_handle, c_uint(b_size), c_resp, byref(c_read))
                temp = c_resp.value
                response += temp[:c_read.value]
                time.sleep(response_time)
                have_data = aotf.AotfIsReadDataAvailable(self.aotf_handle)
            return response
        else:
            return "Invalid"

    def _aotfOpen(self):
        try:
            self.aotf_handle = aotf.AotfOpen(0)
            self._aotfSendCmd("dau en")
            return 1
        except:
            return 0

    def _aotfSendCmd(self, cmd):
        if self.live:
            cmd += "\n"
            assert aotf.AotfWrite(self.aotf_handle, c_uint(len(cmd)), c_char_p(cmd)) == 1, "aotfSendCMD failed!"

    def _sendCmd(self, cmd):
        self._aotfSendCmd(cmd)
        response = self._aotfGetResp()
        bad_response = "Invalid"
        if response[0:len(bad_response)] == bad_response:
            print "AOTF Warning:", response
        else:
            return response

    # If you don't call this then the program will lock on shutdown
    # (at least when run from the DOS prompt).
    def _shutDown(self):
        if self.live:
            self._aotfSendCmd("dds Reset")
            self._aotfGetResp()
            aotf.AotfClose(self.aotf_handle)

    def analogModulationOn(self):
        self._sendCmd("dau dis")

    def analogModulationOff(self):
        self._sendCmd("dau en")

    def fskOff(self, channel):
        cmd = "dds fsk " + str(channel) + " 0"
        self._sendCmd(cmd)

    def fskOn(self, channel):
        cmd = "dds fsk " + str(channel) + " 1"
        self._sendCmd(cmd)

    def getStatus(self):
        return self.live

    def reset(self):
        self._sendCmd("dds Reset")

    def setAmplitude(self, channel, amplitude):
        assert channel >= 0, "setAmplitude: channel out of range " + str(channel)
        assert channel < 8, "setAmplitude: channel out of range " + str(channel)
        assert amplitude >= 0, "setAmplitude: amplitude out of range " + str(amplitude)
        assert amplitude <= 16383, "setAmplitude: amplitude out of range " + str(amplitude)
        cmd = "dds a " + str(channel) + " " + str(amplitude)
        self._sendCmd(cmd)

    def setChannel(self, channel, frequency, amplitude):
        self.setFrequency(channel, frequency)
        self.setAmplitude(channel, amplitude)

    def setFrequencies(self, channel, frequencies):
        assert channel >= 0, "setFrequencies: channel out of range " + str(channel)
        assert channel < 8, "setFrequencies: channel out of range " + str(channel)
        frequency_string = ""
        for frequency in frequencies:
            assert frequency >= 0, "setFrequencies: frequency out of range " + str(frequency)
            assert frequency < 160.0, "setFrequencies: frequency out of range " + str(frequency)
            frequency_string += " " + str(frequency)
        cmd = "dds f " + str(channel) + frequency_string
        self._sendCmd(cmd)

    def setFrequency(self, channel, frequency):
        self.setFrequencies(channel, [frequency])

    def shutDown(self):
        global instantiated
        instantiated = 0
        self._shutDown()
        self.aotf_handle = 0

#    def __del__(self):
#        if self.aotf_handle:
#            self.shutDown()
    

#
# Testing.
#

if __name__ == "__main__":
    my_aotf = AOTF()
    print my_aotf._sendCmd("BoardID ID")
    print my_aotf._sendCmd("help adc")
    my_aotf.shutDown()


#
# The MIT License
#
# Copyright (c) 2009 Zhuang Lab, Harvard University
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
 
