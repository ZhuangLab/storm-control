#!/usr/bin/python
#
## @file
#
# Generic Coherent Cube laser control (via RS-232)
#
# Hazen 7/10
#

import sc_hardware.serial.RS232 as RS232
import time

## Cube
#
# This class controls a Coherent cube laser using RS-232 communication.
#
class Cube(RS232.RS232):

    ## __init__
    #
    # Connect to the laser by RS-232 and verify that the connection has been made.
    #
    # @param port The RS-232 port that the laser is on. This is a string like "COM9".
    #
    def __init__(self, port):
        self.on = False
        try:
            # open port
            RS232.RS232.__init__(self, port, None, 19200, "\r", 0.05)

            # see if the laser is connected
            assert not(self.commWithResp("?HID") == None)

            # finish setup
            self.pmin = 0.0
            self.pmax = 5.0
            [self.pmin, self.pmax] = self.getPowerRange()
            self.setExtControl(0)
            if (not self.getLaserOnOff()):
                self.setLaserOnOff(True)
        except:
            self.live = False
            print "Failed to connect to Cube Laser at port", port
            print "Perhaps it is turned off or the COM ports have"
            print "been scrambled?"

    ## respToFloat
    #
    # Convert a response from the laser to a floating point number.
    #
    # @param resp The response string from the laser.
    # @param start The index of the first character in the number.
    #
    # @return A floating point number.
    #
    def respToFloat(self, resp, start):
        return float(resp[start:-1])

    ## getExtControl
    #
    # Checks if the laser is configured for external control.
    #
    # @return True/False
    #
    def getExtControl(self):
        self.sendCommand("?EXT")
        response = self.waitResponse()
        if response.find("=1") == -1:
            return False
        else:
            return True

    ## getLaserOnOff
    #
    # Checks if the laser is on or off.
    #
    # @return True/False
    #
    def getLaserOnOff(self):
        self.sendCommand("?L")
        resp = self.waitResponse()
        if (resp[2] == "1"):
            self.on = True
            return True
        else:
            self.on = False
            return False

    ## getPowerRange
    #
    # Returns the laser power range (in mW?).
    #
    # @return [minimum power, maximum power]
    #
    def getPowerRange(self):
        self.sendCommand("?MINLP")
        pmin = self.respToFloat(self.waitResponse(), 6)
        self.sendCommand("?MAXLP")
        pmax = self.respToFloat(self.waitResponse(), 6)
        return [pmin, pmax]

    ## getPower
    #
    # Return the current laser power (in mW?).
    #
    # @return The laser power as a float.
    #
    def getPower(self):
        self.sendCommand("?SP")
        power_string = self.waitResponse()
        return float(power_string[3:-1])

    ## setExtControl
    #
    # Set the laser to external control mode.
    #
    # @param mode True/False turn on/off external control mode.
    #
    def setExtControl(self, mode):
        if mode:
            self.sendCommand("EXT=1")
        else:
            self.sendCommand("EXT=0")
        self.waitResponse()

    ## setLaserOnOff
    #
    # Turn the laser on or off.
    #
    # @param on True/False, turn the laser on/off
    #
    def setLaserOnOff(self, on):
        if on and (not self.on):
            self.sendCommand("L=1")
            self.waitResponse()
            self.on = True
        if (not on) and self.on:
            self.sendCommand("L=0")
            self.waitResponse()
            self.on = False

    ## setPower
    #
    # Set the laser power (in mW).
    #
    # @param power_in_mw The desired laser power in mW.
    #
    def setPower(self, power_in_mw):
        if power_in_mw > self.pmax:
            power_in_mw = self.pmax
        self.sendCommand("P=" + str(power_in_mw))
        self.waitResponse()

    ## shutDown
    #
    # Turn the laser off & close the RS-232 connection.
    #
    def shutDown(self):
        if self.live:
            self.setLaserOnOff(False)
        RS232.RS232.shutDown(self)

#
# Testing
#

if __name__ == "__main__":
    cube = Cube("COM1")
    if cube.getStatus():
        print cube.getPowerRange()
        print cube.getLaserOnOff()
        cube.shutDown()

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

