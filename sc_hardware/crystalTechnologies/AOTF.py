#!/usr/bin/python
#
## @file
#
# Communicates with the Crystal Technologies AOTF (via USB).
#
# To work around the lack of a 64 bit version of the
# AotfLibrary.dll file we handle a aotf communication
# using the AOTF32Bit.py script which needs to be
# run in 32 bit Python. Then we communicate with it
# using basic IPC.
#
# Hazen 12/13
#

from ctypes import *
import os
import socket
import subprocess
import time

aotf = None
response_time = 0.05
instantiated = 0

## AOTF
#
# This class handles communication with a Crystal Technologies AOTF.
#
# FIXME: I'd like for this class to make sure that the AOTF is closed
# For now, you have to make sure shutdown is called or the process will
# lock (or at least it will lock the DOS prompt).
#
class AOTF():

    ## __init__
    #
    # Create a AOTF object, load the DLL that is used to control the AOTF
    # and verify that we can talk to the AOTF.
    #
    # FIXME: Is the instantiated stuff necessary? It doesn't seem likely
    #    that we'd ever make the mistake of trying to create two of
    #    these classes in a single process.
    #
    def __init__(self):
        self.live = 1

        global instantiated
        if instantiated:
            print "Attempt to instantiate two AOTF communication classes."
            self.live = False
        else:
            # Load the AOTF driver library library.
            global aotf
            if os.path.exists('C:\Program Files\Crystal Technology\AOTF Utilities\AotfLibrary\LegacyAotfLibrary\DLL\AotfLibrary.dll'):
                aotf = cdll.LoadLibrary('C:\Program Files\Crystal Technology\AOTF Utilities\AotfLibrary\LegacyAotfLibrary\DLL\AotfLibrary')
            elif os.path.exists('C:\Program Files\Crystal Technology\Developer\AotfLibrary\DLL\AotfLibrary.dll'):
                aotf = cdll.LoadLibrary('C:\Program Files\Crystal Technology\Developer\AotfLibrary\DLL\AotfLibrary')
            else:
                print "Failed to load AotfLibrary.dll"

            if self._aotfOpen():
                self.live = True
                instantiated = True
            else:
                print "Failed to connect to the AOTF, perhaps it is turned off?"
                self.live = False

    ## _aotfGetResp
    #
    # This gets a response from the AOTF. If the AOTF does not respond with any data
    # in response_time (50ms) then it assumes that there is no more data to get
    # from the AOTF.
    #
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

    ## _aotfOpen
    #
    # The checks whether the AOTF is "open", i.e. that we can talk to it.
    #
    # @return True/False, we can talk to the AOTF.
    #
    def _aotfOpen(self):
        try:
            self.aotf_handle = aotf.AotfOpen(0)
            self._aotfSendCmd("dau en")
            self._sendCmd("dau gain * 255")
            return True
        except:
            return False

    ## _aotfSendCmd
    #
    # Sends a command to the AOTF.
    #
    # @param cmd The command to send (as a string).
    #
    def _aotfSendCmd(self, cmd):
        if self.live:
            cmd += "\n"
            assert aotf.AotfWrite(self.aotf_handle, c_uint(len(cmd)), c_char_p(cmd)) == 1, "aotfSendCMD failed!"

    ## _sendCmd
    #
    # Sends a command to the AOTF and waits for a response.
    #
    # @param cmd The command to send (as a string).
    #
    # @return The response from the AOTF, or a warning message if the response was bad.
    #
    def _sendCmd(self, cmd):
        self._aotfSendCmd(cmd)
        response = self._aotfGetResp()
        bad_response = "Invalid"
        if response[0:len(bad_response)] == bad_response:
            print "AOTF Warning:", response
        else:
            return response

    ## _shutDown
    #
    # If you don't call this then the program will lock on shutdown. The only
    # way to unlock it is to run the Crystal Technologies labview AOTF control
    # program.
    #
    def _shutDown(self):
        if self.live:
            self._aotfSendCmd("dds Reset")
            self._aotfGetResp()
            aotf.AotfClose(self.aotf_handle)

    ## analogModulationOn
    #
    # Turn on analog modulation of the AOTF.
    #
    def analogModulationOn(self):
        self._sendCmd("dau dis")

    ## analogModulationOff
    #
    # Turn off analog modulation of the AOTF.
    #
    def analogModulationOff(self):
        self._sendCmd("dau en")

    ## fskOff
    #
    # Turn frequency shift key off for the specified channel.
    #
    # @param channel Turn FSK off for this channel.
    #
    def fskOff(self, channel):
        cmd = "dds fsk " + str(channel) + " 0"
        self._sendCmd(cmd)

    ## fskOn
    #
    # Turn frequency shift key on for the specified channel.
    #
    # @param channel Turn FSK on for this channel.
    #
    def fskOn(self, channel, mode = 1):
        cmd = "dds fsk " + str(channel) + " " + str(mode)
        self._sendCmd(cmd)

    ## getStatus
    #
    # @return True/False, we can talk to the AOTF.
    #
    def getStatus(self):
        return self.live

    ## reset
    #
    # Resets the AOTF.
    #
    def reset(self):
        self._sendCmd("dds Reset")

    ## setAmplitude
    #
    # Sets amplitude of the specified channel.
    #
    # @param channel The channel to set.
    # @param amplitude The desired amplitude value.
    #
    def setAmplitude(self, channel, amplitude):
        assert channel >= 0, "setAmplitude: channel out of range " + str(channel)
        assert channel < 8, "setAmplitude: channel out of range " + str(channel)
        assert amplitude >= 0, "setAmplitude: amplitude out of range " + str(amplitude)
        assert amplitude <= 16383, "setAmplitude: amplitude out of range " + str(amplitude)
        cmd = "dds a " + str(channel) + " " + str(amplitude)
        self._sendCmd(cmd)

    ## setChannel
    #
    # Sets the frequency and the amplitude of the specified channel.
    #
    # @param channel The channel to set.
    # @param frequency The desired frequency.
    # @param amplitude The desired amplitude.
    #
    def setChannel(self, channel, frequency, amplitude):
        self.setFrequency(channel, frequency)
        self.setAmplitude(channel, amplitude)

    ## setFrequencies
    #
    # Sets the frequencies of the specified channel.
    #
    # @param channel The channel to set.
    # @param frequencies A python array of frequencies.
    #
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

    ## setFrequency
    #
    # Set the frequency of the specified channel. 
    #
    # @param channel The channel to set.
    # @param frequency The desired frequency.
    #
    def setFrequency(self, channel, frequency):
        self.setFrequencies(channel, [frequency])

    ## shutDown
    #
    # Reset the AOTF and shutdown communication.
    #
    def shutDown(self):
        global instantiated
        instantiated = False
        self._shutDown()
        self.aotf_handle = False

#    def __del__(self):
#        if self.aotf_handle:
#            self.shutDown()

## AOTF64Bit
#
# This class is for communication with a AOTF when running
# 64 bit Python. Since the provided driver only works with
# 32 bit processes we start a 32 bit Python process to
# control the AOTF, then we talk to it via IPC (port #9001).
#
# FIXME: Should there be time-outs on the connection?
#
class AOTF64Bit(AOTF):

    ## __init__
    #
    # Create a 32 bit process for communication with the AOTF and
    # verify that it can talk to the AOTF.
    #
    def __init__(self):

        # Create socket.
        self.aotf_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#        self.aotf_socket.settimeout(1.0)
        self.aotf_socket.bind(("127.0.0.1", 9001))

        # Create sub-process to control the AOTF.
        dir = os.path.dirname(__file__)
        if (len(dir) > 0):
            self.aotf_cmd = dir + "\AOTF32Bit.py"
        else:
            self.aotf_cmd = "AOTF32Bit.py"

        self.live = True
        self.aotf_proc = subprocess.Popen(["c:\python27_32bit\python", self.aotf_cmd], close_fds = True)

        # Wait for connection from the sub-process.
        self.aotf_socket.listen(1)
        [self.aotf_conn, self.aotf_addr] = self.aotf_socket.accept()

        # Verify that we can talk to the AOTF (through the sub-process).
        if not self._aotfOpen():
            self.live = False

    ## _aotfOpen
    #
    # @return True/False we can talk to the AOTF.
    #
    def _aotfOpen(self):
        response = self._sendCmd("dau en")
        if ("Invalid" in response):
            return False
        else:
            self._sendCmd("dau gain * 255")
            return True

    ## _sendCmd
    #
    # Send a command to the AOTF using IPC.
    #
    # @param cmd The command to send (a string).
    #
    # @return The response of "Invalid" if there was a problem.
    #    
    def _sendCmd(self, cmd):
        if self.live:
            self.aotf_conn.sendall(cmd)
            resp = self.aotf_conn.recv(1024)
            return resp

            #self.aotf_proc.stdin.write(cmd + "\n")
            #self.aotf_proc.stdin.flush()
            #resp = self.aotf_proc.stdout.readline()
            # This removes both \r and the \n.."
            #resp = resp[:-2] if resp.endswith('\n') else resp
            #return resp
        else:
            return "Invalid"

    ## shutDown
    #
    # Reset the AOTF and shutdown IPC.
    #
    def shutDown(self):
        self._sendCmd("shutdown")
        self.aotf_conn.close()
        self.aotf_proc.terminate()
        
#
# Testing.
#

if __name__ == "__main__":
    my_aotf = AOTF64Bit()
    print my_aotf._sendCmd("BoardID ID")
    print my_aotf._sendCmd("dds f 0 88.6")
    print my_aotf._sendCmd("dds a 0 6100")
    time.sleep(1.0)
    my_aotf.shutDown()

#
# The MIT License
#
# Copyright (c) 2013 Zhuang Lab, Harvard University
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
 
