#!/usr/bin/env python
"""
Generic Coherent Cube laser control (via RS-232)

Hazen 7/10
"""
import traceback

import storm_control.sc_hardware.serial.RS232 as RS232

class Cube(RS232.RS232):
    """
    This class controls a Coherent cube laser using RS-232 communication.
    """
    def __init__(self, **kwds):
        """
        Connect to the laser by RS-232 and verify that the connection has been made.
        """
        # Add Cube RS232 default settings.
        kwds["baudrate"] = 19200
        kwds["end_of_line"] = "\r"
        kwds["wait_time"] = 0.05

        self.on = False
        self.pmin = 0.0
        self.pmax = 5.0
        
        try:
            # open port
            super().__init__(**kwds)

            # see if the laser is connected
            assert not(self.commWithResp("?HID") == None)

        # FIXME: This should not catch everything!
        except Exception:
            print(traceback.format_exc())
            self.live = False
            print("Failed to connect to Cube Laser at port", kwds["port"])
            print("Perhaps it is turned off or the COM ports have")
            print("been scrambled?")
            
        if self.live:
            [self.pmin, self.pmax] = self.getPowerRange()
            self.setExtControl(0)
            if (not self.getLaserOnOff()):
                self.setLaserOnOff(True)

    def respToFloat(self, resp, start):
        """
        Convert a response from the laser to a floating point number.
        """
        return float(resp[start:-1])

    def getExtControl(self):
        """
        Checks if the laser is configured for external control.
        """
        self.sendCommand("?EXT")
        response = self.waitResponse()
        if (response.find("=1") == -1):
            return False
        else:
            return True

    def getLaserOnOff(self):
        """
        Checks if the laser is on or off.
        """
        self.sendCommand("?L")
        resp = self.waitResponse()
        if (resp[2] == "1"):
            self.on = True
            return True
        else:
            self.on = False
            return False

    def getPowerRange(self):
        """
        Returns the laser power range (in mW?).
        """
        self.sendCommand("?MINLP")
        pmin = self.respToFloat(self.waitResponse(), 6)
        self.sendCommand("?MAXLP")
        pmax = self.respToFloat(self.waitResponse(), 6)
        return [pmin, pmax]

    def getPower(self):
        """
        Return the current laser power (in mW?).
        """
        self.sendCommand("?SP")
        power_string = self.waitResponse()
        return float(power_string[3:-1])

    def setExtControl(self, mode):
        """
        Set the laser to external control mode.
        """
        if mode:
            self.sendCommand("EXT=1")
        else:
            self.sendCommand("EXT=0")
        self.waitResponse()

    def setLaserOnOff(self, on):
        """
        Turn the laser on or off.
        """
        if on and (not self.on):
            self.sendCommand("L=1")
            self.waitResponse()
            self.on = True
        if (not on) and self.on:
            self.sendCommand("L=0")
            self.waitResponse()
            self.on = False

    def setPower(self, power_in_mw):
        """
        Set the laser power (in mW).
        """
        if power_in_mw > self.pmax:
            power_in_mw = self.pmax
        self.sendCommand("P=" + str(power_in_mw))
        self.waitResponse()

    def shutDown(self):
        """
        Turn the laser off & close the RS-232 connection.
        """
        if self.live:
            self.setLaserOnOff(False)
        super().shutDown()

        
#
# Testing
#
if (__name__ == "__main__"):
    cube = Cube(port = "COM10")
    if cube.getStatus():
        print(cube.getPowerRange())
        print(cube.getLaserOnOff())
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

