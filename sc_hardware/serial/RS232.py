#!/usr/bin/python
#
## @file
#
# Wraps the uspp library for RS232 communication.
#
# Hazen 3/09
#

import uspp.uspp as uspp
import time

## RS232
#
# The basic RS-232 communication object which is used by all the objects
# that communicate with their associated hardware using RS-232.
#
class RS232():

    ## __init__
    #
    # @param port The port for RS-232 communication, e.g. "COM4".
    # @param timeout The time out value for communication.
    # @param baudrate The RS-232 communication speed, e.g. 9800.
    # @param end_of_line What character(s) are used to indicate the end of a line.
    # @param wait_time How long to wait between polling events before it is decided that there is no new data available on the port.
    #
    def __init__(self, port, timeout, baudrate, end_of_line, wait_time):
        try:
            self.tty = uspp.SerialPort(port, timeout, baudrate)
            self.tty.flush()
            self.end_of_line = end_of_line
            self.wait_time = wait_time
            self.live = True
            time.sleep(self.wait_time)
        except Exception as e:
            print "RS232 Error:", type(e), str(e)
            self.live = False

    ## commWithResp
    #
    # Send a command and wait (a little) for a response.
    #
    # @param command The command to send (as a string).
    #
    # @return The response from the hardware (if any).
    #
    def commWithResp(self, command):
        self.tty.flush()
        self.tty.write(command + self.end_of_line)
        time.sleep(10 * self.wait_time)
        response = ""
        response_len = self.tty.inWaiting()
        while response_len:
            response += self.tty.read(response_len)
            time.sleep(self.wait_time)
            response_len = self.tty.inWaiting()
        if len(response) > 0:
            return response

    ## getResponse
    #
    # Wait (a little) for a response.
    #
    # @return The response from the hardware (if any).
    #
    def getResponse(self):
        response = ""
        response_len = self.tty.inWaiting()
        while response_len:
            response += self.tty.read(response_len)
            time.sleep(self.wait_time)
            response_len = self.tty.inWaiting()
        if len(response) > 0:
            return response

    ## getStatus
    #
    # @return True/False is the port open and can we talk to the hardware.
    #
    def getStatus(self):
        return self.live

    ## sendCommand
    #
    # @param command The command to send to the hardware.
    #
    def sendCommand(self, command):
        self.tty.flush()
        self.tty.write(command + self.end_of_line)

    ## shutDown
    #
    # Closes the RS-232 port.
    #
    def shutDown(self):
        if self.live and hasattr(self, "tty"):
            del(self.tty)

    ## waitResponse
    #
    # Waits much longer for a response. This is the method to use if
    # you are sure that the hardware will respond eventually. If you
    # don't set end_of_response then it will automatically be the
    # end_of_line character, and this will return once it finds the
    # first end_of_line character.
    #
    # @param end_of_response (Optional) The expected character(s) at the end of the response string, defaults to end_of_line.
    # @param max_attempts (Optional) How many cycles of polling to undertake before giving up, defaults to 200.
    #
    # @return The response from the hardware (if any).
    #
    def waitResponse(self, end_of_response = False, max_attempts = 200):
        if not end_of_response:
            end_of_response = str(self.end_of_line)
        attempts = 0
        response = ""
        index = -1
        while (index == -1) and (attempts < max_attempts):
            response_len = self.tty.inWaiting()
            if response_len > 0:
                response += self.tty.read(response_len)
            time.sleep(self.wait_time)
            index = response.find(end_of_response)
            attempts += 1
        return response


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

